"""Diğer bounded context'lerden gelen integration event'lerin işlenmesi."""

import logging
from typing import Any

from app.application.commands.handlers import PostCommandHandler

log = logging.getLogger(__name__)


class CommentEventsHandler:
    def __init__(self, commands: PostCommandHandler) -> None:
        self._commands = commands

    def __call__(self, envelope: dict[str, Any]) -> None:
        event_type = envelope.get("event_type")
        payload = envelope.get("payload") or {}
        if event_type in ("comment.approved", "comment.rejected", "comment.deleted"):
            self._commands.sync_comment_count(payload["post_id"], int(payload.get("approved_comment_count", 0)))
            log.info("Yorum sayısı senkronize edildi", extra={"post_id": payload["post_id"], "event_type": event_type})
