"""Dayanıklı RabbitMQ tüketicisi: otomatik yeniden bağlanma, idempotency, poison-message -> DLQ."""

import contextlib
import json
import logging
import threading
import time
from collections.abc import Callable
from typing import Any

import pika

from ..backoff import Backoff
from ..correlation import reset_correlation_id, set_correlation_id
from .topology import declare_topology

log = logging.getLogger(__name__)
Handler = Callable[[dict[str, Any]], None]


class RabbitMqConsumer:
    def __init__(
        self,
        url: str,
        queue: str,
        handler: Handler,
        redis_client=None,
        prefetch: int = 10,
        on_processed: Callable[[str, str], None] | None = None,
    ) -> None:
        self._url = url
        self._queue = queue
        self._handler = handler
        self._redis = redis_client
        self._prefetch = prefetch
        self._on_processed = on_processed
        self._stopping = threading.Event()
        self._connection: pika.BlockingConnection | None = None
        self._channel = None
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------ lifecycle
    def start(self) -> None:
        self._thread = threading.Thread(target=self.run_forever, name=f"consumer-{self._queue}", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stopping.set()
        conn, ch = self._connection, self._channel
        if conn and conn.is_open and ch:
            with contextlib.suppress(Exception):  # kapanış sırasında en iyi çaba
                conn.add_callback_threadsafe(ch.stop_consuming)
        if self._thread:
            self._thread.join(timeout=5)

    def run_forever(self) -> None:
        backoff = Backoff()
        while not self._stopping.is_set():
            try:
                params = pika.URLParameters(self._url)
                params.heartbeat = 30
                self._connection = pika.BlockingConnection(params)
                self._channel = self._connection.channel()
                declare_topology(self._channel)
                self._channel.basic_qos(prefetch_count=self._prefetch)
                self._channel.basic_consume(queue=self._queue, on_message_callback=self._on_message)
                log.info("Kuyruk dinleniyor", extra={"queue": self._queue})
                backoff.reset()
                self._channel.start_consuming()
            except Exception as exc:  # noqa: BLE001
                if self._stopping.is_set():
                    break
                delay = backoff.next_delay()
                if backoff.attempt <= 3 or backoff.attempt % 10 == 0:
                    log.warning(
                        "Consumer bağlantısı yok, tekrar denenecek",
                        extra={
                            "queue": self._queue,
                            "error": str(exc)[:300] or type(exc).__name__,
                            "attempt": backoff.attempt,
                            "retry_in_s": round(delay, 1),
                        },
                    )
                self._stopping.wait(delay)
            finally:
                with contextlib.suppress(Exception):  # kapanış sırasında en iyi çaba
                    if self._connection and self._connection.is_open:
                        self._connection.close()

    # ------------------------------------------------------------ handling
    def _idem_key(self, event_id: str) -> str:
        return f"idem:{self._queue}:{event_id}"

    def _already_processed(self, event_id: str) -> bool:
        if not self._redis or not event_id:
            return False
        try:
            return bool(self._redis.exists(self._idem_key(event_id)))
        except Exception:  # noqa: BLE001
            return False

    def _mark_processed(self, event_id: str) -> None:
        if not self._redis or not event_id:
            return
        try:
            self._redis.set(self._idem_key(event_id), "1", ex=7 * 24 * 3600)
        except Exception:  # noqa: BLE001
            log.warning("Idempotency anahtarı yazılamadı")

    def _on_message(self, channel, method, properties, body: bytes) -> None:
        try:
            envelope = json.loads(body)
        except ValueError:
            log.error("Geçersiz JSON mesajı DLQ'ya gönderiliyor", extra={"queue": self._queue})
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        token = set_correlation_id(envelope.get("correlation_id"))
        event_id = envelope.get("event_id", "")
        event_type = envelope.get("event_type", method.routing_key)
        try:
            if self._already_processed(event_id):
                log.info("Tekrarlanan event atlandı", extra={"event_id": event_id, "event_type": event_type})
                channel.basic_ack(delivery_tag=method.delivery_tag)
                return
            self.handle(envelope)
            self._mark_processed(event_id)
            channel.basic_ack(delivery_tag=method.delivery_tag)
            if self._on_processed:
                self._on_processed(event_type, "success")
        except Exception:  # noqa: BLE001
            log.exception("Event işlenemedi, yeniden kuyruğa alınıyor", extra={"event_type": event_type})
            if self._on_processed:
                self._on_processed(event_type, "failure")
            time.sleep(1)
            # quorum queue x-delivery-limit aşılınca mesaj otomatik olarak DLQ'ya düşer
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            reset_correlation_id(token)

    def handle(self, envelope: dict[str, Any]) -> None:
        self._handler(envelope)
