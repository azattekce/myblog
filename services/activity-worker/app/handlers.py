"""Tüm domain olaylarını dinleyerek audit/aktivite akışı ve bildirimler üretir.

Gerçek bir e-posta/Slack entegrasyonu eklemek için Notifier arayüzünü implemente etmek yeterlidir.
"""

import logging
from typing import Any, Protocol

from prometheus_client import Counter

log = logging.getLogger("activity")

EVENTS_CONSUMED = Counter("devblog_events_consumed_total", "Tüketilen domain event sayısı", ["event_type", "source"])


class Notifier(Protocol):
    def notify(self, subject: str, body: str) -> None: ...


class LogNotifier:
    def notify(self, subject: str, body: str) -> None:
        log.info("Bildirim gönderildi", extra={"channel": "log", "subject": subject, "body": body})


class ActivityHandler:
    def __init__(self, notifier: Notifier) -> None:
        self._notifier = notifier

    def __call__(self, envelope: dict[str, Any]) -> None:
        event_type = envelope.get("event_type", "unknown")
        source = envelope.get("source", "unknown")
        payload = envelope.get("payload") or {}
        EVENTS_CONSUMED.labels(event_type=event_type, source=source).inc()
        log.info(
            "Domain event",
            extra={
                "event_type": event_type,
                "source": source,
                "event_id": envelope.get("event_id"),
                "audit_payload": payload,
            },
        )

        if event_type == "comment.created":
            self._notifier.notify(
                "Moderasyon bekleyen yeni yorum",
                f"{payload.get('author_name')} bir yorum yazdı (post: {payload.get('post_id')})",
            )
        elif event_type == "post.published":
            self._notifier.notify("Yazı yayınlandı", f"'{payload.get('title')}' yayında: /posts/{payload.get('slug')}")
        elif event_type == "user.logged_in":
            self._notifier.notify(
                "Yönetim paneline giriş", f"{payload.get('username')} giriş yaptı ({payload.get('ip')})"
            )
