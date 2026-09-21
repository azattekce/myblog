from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from devblog_common.clock import utcnow
from devblog_common.domain import AggregateRoot, BusinessRuleViolation, new_id

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class CommentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class Comment(AggregateRoot):
    id: str
    post_id: str
    author_name: str
    content: str
    author_email: str | None = None
    status: CommentStatus = CommentStatus.PENDING
    ip_hash: str | None = None
    created_at: datetime = field(default_factory=utcnow)
    moderated_at: datetime | None = None

    @classmethod
    def submit(
        cls, post_id: str, author_name: str, content: str, author_email: str | None, ip_hash: str | None
    ) -> Comment:
        name, text = author_name.strip(), content.strip()
        if not 2 <= len(name) <= 60:
            raise BusinessRuleViolation("İsim 2-60 karakter olmalı")
        if not 3 <= len(text) <= 2000:
            raise BusinessRuleViolation("Yorum 3-2000 karakter olmalı")
        if author_email and not _EMAIL.match(author_email):
            raise BusinessRuleViolation("Geçerli bir e-posta girin")
        c = cls(
            id=new_id(),
            post_id=post_id,
            author_name=name,
            content=text,
            author_email=(author_email or None),
            ip_hash=ip_hash,
        )
        c.record_event("comment.created", {"comment_id": c.id, "post_id": post_id, "author_name": name})
        return c

    # Onaylı yorum sayısı, olay yükünde mutlak değer olarak taşınır -> tüketici tarafında idempotent.
    def approve(self, current_approved_count: int) -> None:
        if self.status == CommentStatus.APPROVED:
            raise BusinessRuleViolation("Yorum zaten onaylı")
        self.status, self.moderated_at = CommentStatus.APPROVED, utcnow()
        self.record_event("comment.approved", self._count_payload(current_approved_count + 1))

    def reject(self, current_approved_count: int) -> None:
        if self.status == CommentStatus.REJECTED:
            raise BusinessRuleViolation("Yorum zaten reddedilmiş")
        was_approved = self.status == CommentStatus.APPROVED
        self.status, self.moderated_at = CommentStatus.REJECTED, utcnow()
        self.record_event("comment.rejected", self._count_payload(current_approved_count - (1 if was_approved else 0)))

    def mark_deleted(self, current_approved_count: int) -> None:
        was_approved = self.status == CommentStatus.APPROVED
        self.record_event("comment.deleted", self._count_payload(current_approved_count - (1 if was_approved else 0)))

    def _count_payload(self, count: int) -> dict:
        return {"comment_id": self.id, "post_id": self.post_id, "approved_comment_count": max(0, count)}


@dataclass
class KnownPost:
    """post-service'ten event'lerle beslenen yerel projeksiyon (senkron servis çağrısı yok)."""

    post_id: str
    slug: str
    title: str
    is_published: bool
