"""Transactional Outbox: event'ler iş verisiyle aynı transaction'da yazılır, relay ile RabbitMQ'ya aktarılır."""

from __future__ import annotations

import logging
import threading

from sqlalchemy import BigInteger, DateTime, Integer, String, UnicodeText, select
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

from ..backoff import Backoff
from ..clock import utcnow

log = logging.getLogger(__name__)


def build_outbox_model(base):
    class OutboxMessage(base):
        __tablename__ = "outbox_messages"

        id: Mapped[int] = mapped_column(
            BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
        )
        event_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
        event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
        payload: Mapped[str] = mapped_column(UnicodeText, nullable=False)
        occurred_at = mapped_column(DateTime, nullable=False)
        published_at = mapped_column(DateTime, nullable=True, index=True)
        attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    return OutboxMessage


class OutboxRelay:
    def __init__(self, session_factory: sessionmaker, model, publisher, interval: float = 1.0, batch_size: int = 100):
        self._session_factory = session_factory
        self._model = model
        self._publisher = publisher
        self._interval = interval
        self._batch_size = batch_size
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name="outbox-relay", daemon=True)
        self._thread.start()
        log.info("Outbox relay başlatıldı")

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._publisher.close()

    def _run(self) -> None:
        backoff = Backoff()
        while not self._stop.is_set():
            published = 0
            try:
                published = self.publish_pending()
                self._publisher.heartbeat()
            except Exception as exc:  # noqa: BLE001
                delay = backoff.next_delay()
                # Uzun kesintide log seli olmasın: ilk denemeler + her 10. deneme loglanır
                if backoff.attempt <= 3 or backoff.attempt % 10 == 0:
                    log.warning(
                        "Outbox yayını başarısız, tekrar denenecek",
                        extra={
                            "error": str(exc)[:300] or type(exc).__name__,
                            "attempt": backoff.attempt,
                            "retry_in_s": round(delay, 1),
                        },
                    )
                self._stop.wait(delay)
                continue
            backoff.reset()
            if published < self._batch_size:
                self._stop.wait(self._interval)

    def publish_pending(self) -> int:
        m = self._model
        with self._session_factory() as session:
            rows = (
                session.execute(select(m).where(m.published_at.is_(None)).order_by(m.id).limit(self._batch_size))
                .scalars()
                .all()
            )
            for row in rows:
                try:
                    self._publisher.publish(row.event_type, row.payload, message_id=row.event_id)
                except Exception:
                    row.attempts += 1
                    session.commit()
                    raise
                row.published_at = utcnow()
                session.commit()
                log.info("Event yayınlandı", extra={"event_type": row.event_type, "event_id": row.event_id})
            return len(rows)
