import contextlib
import logging
import threading

import pika

from .topology import EVENTS_EXCHANGE, declare_topology

log = logging.getLogger(__name__)


class NullPublisher:
    """Mesajlaşma kapalıyken (testler) kullanılan no-op publisher."""

    def __init__(self) -> None:
        self.published: list[tuple[str, str]] = []

    def publish(self, routing_key: str, body: str, message_id: str) -> None:
        self.published.append((routing_key, body))

    def heartbeat(self) -> None:
        pass

    def close(self) -> None:
        pass


class RabbitMqPublisher:
    """Publisher confirms + persistent mesajlar ile güvenilir yayın."""

    def __init__(self, url: str, app_id: str) -> None:
        self._url = url
        self._app_id = app_id
        self._connection: pika.BlockingConnection | None = None
        self._channel = None
        self._lock = threading.Lock()

    def _ensure(self) -> None:
        if self._connection and self._connection.is_open and self._channel and self._channel.is_open:
            return
        params = pika.URLParameters(self._url)
        params.heartbeat = 30
        params.blocked_connection_timeout = 30
        self._connection = pika.BlockingConnection(params)
        self._channel = self._connection.channel()
        self._channel.confirm_delivery()
        declare_topology(self._channel)
        log.info("RabbitMQ publisher bağlandı")

    def publish(self, routing_key: str, body: str, message_id: str) -> None:
        with self._lock:
            try:
                self._ensure()
                self._channel.basic_publish(
                    exchange=EVENTS_EXCHANGE,
                    routing_key=routing_key,
                    body=body.encode("utf-8"),
                    properties=pika.BasicProperties(
                        content_type="application/json",
                        delivery_mode=pika.DeliveryMode.Persistent,
                        message_id=message_id,
                        type=routing_key,
                        app_id=self._app_id,
                    ),
                )
            except Exception:
                self._reset()
                raise

    def heartbeat(self) -> None:
        with self._lock:
            if self._connection and self._connection.is_open:
                try:
                    self._connection.process_data_events(time_limit=0)
                except Exception:  # noqa: BLE001
                    self._reset()

    def _reset(self) -> None:
        with contextlib.suppress(Exception):  # kapanış sırasında en iyi çaba
            if self._connection and self._connection.is_open:
                self._connection.close()
        self._connection = None
        self._channel = None

    def close(self) -> None:
        with self._lock:
            self._reset()
