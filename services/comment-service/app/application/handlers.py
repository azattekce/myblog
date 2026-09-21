import hashlib
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from app.domain.comment import Comment, KnownPost
from app.domain.repositories import CommentRepository, KnownPostRepository
from devblog_common.cache import RedisCache
from devblog_common.domain import BusinessRuleViolation, NotFoundError, RateLimitedError

log = logging.getLogger(__name__)
CACHE_NS = "comments"


class CommentUnitOfWork(Protocol):
    comments: CommentRepository
    known_posts: KnownPostRepository

    def __enter__(self) -> "CommentUnitOfWork": ...
    def __exit__(self, *args) -> None: ...
    def commit(self) -> None: ...
    def on_commit(self, cb) -> None: ...


class RateLimiter(Protocol):
    def allow(self, key: str) -> bool: ...


class CommentReadModel(Protocol):
    def approved_for_post(self, post_id: str) -> list[dict[str, Any]]: ...
    def admin_list(self, status: str | None, page: int, size: int) -> dict[str, Any]: ...
    def counts(self) -> dict[str, int]: ...


@dataclass(frozen=True)
class SubmitCommentCommand:
    post_id: str
    author_name: str
    content: str
    author_email: str | None
    ip: str | None
    honeypot: str | None = None


class CommentCommandHandler:
    def __init__(
        self, uow_factory: Callable[[], CommentUnitOfWork], limiter: RateLimiter, cache: RedisCache, ip_salt: str
    ) -> None:
        self._uow = uow_factory
        self._limiter = limiter
        self._cache = cache
        self._salt = ip_salt

    def _hash_ip(self, ip: str | None) -> str | None:
        # KVKK/GDPR: IP adresi açık halde saklanmaz.
        return hashlib.sha256(f"{self._salt}:{ip}".encode()).hexdigest()[:32] if ip else None

    def submit(self, cmd: SubmitCommentCommand) -> str:
        if cmd.honeypot:
            raise BusinessRuleViolation("Yorum gönderilemedi")
        ip_hash = self._hash_ip(cmd.ip)
        if ip_hash and not self._limiter.allow(ip_hash):
            raise RateLimitedError("Çok sık yorum gönderdiniz, biraz bekleyin")
        with self._uow() as uow:
            post = uow.known_posts.get(cmd.post_id)
            if post is None or not post.is_published:
                raise NotFoundError("Yorum yapılacak yazı bulunamadı")
            comment = Comment.submit(cmd.post_id, cmd.author_name, cmd.content, cmd.author_email, ip_hash)
            uow.comments.add(comment)
            uow.commit()
            log.info("Yorum moderasyon için alındı", extra={"comment_id": comment.id, "post_id": cmd.post_id})
            return comment.id

    def _moderate(self, comment_id: str, action: str) -> None:
        with self._uow() as uow:
            comment = uow.comments.get(comment_id)
            if comment is None:
                raise NotFoundError("Yorum bulunamadı")
            count = uow.comments.count_approved(comment.post_id)
            if action == "approve":
                comment.approve(count)
                uow.comments.update(comment)
            elif action == "reject":
                comment.reject(count)
                uow.comments.update(comment)
            else:
                comment.mark_deleted(count)
                uow.comments.delete(comment)
            uow.on_commit(lambda: self._cache.bump(CACHE_NS))
            uow.commit()

    def approve(self, comment_id: str) -> None:
        self._moderate(comment_id, "approve")

    def reject(self, comment_id: str) -> None:
        self._moderate(comment_id, "reject")

    def delete(self, comment_id: str) -> None:
        self._moderate(comment_id, "delete")


class PostEventsHandler:
    """post-service integration event'leri -> yerel KnownPost projeksiyonu."""

    def __init__(self, uow_factory: Callable[[], CommentUnitOfWork], cache: RedisCache) -> None:
        self._uow = uow_factory
        self._cache = cache

    def __call__(self, envelope: dict[str, Any]) -> None:
        event_type = envelope.get("event_type")
        p = envelope.get("payload") or {}
        with self._uow() as uow:
            if event_type == "post.deleted":
                removed = uow.comments.delete_for_post(p["post_id"])
                uow.known_posts.delete(p["post_id"])
                log.info("Silinen yazının yorumları temizlendi", extra={"post_id": p["post_id"], "removed": removed})
            elif event_type in ("post.published", "post.updated", "post.unpublished"):
                uow.known_posts.upsert(
                    KnownPost(
                        post_id=p["post_id"],
                        slug=p.get("slug", ""),
                        title=p.get("title", ""),
                        is_published=p.get("status") == "published",
                    )
                )
            else:
                return
            uow.on_commit(lambda: self._cache.bump(CACHE_NS))
            uow.commit()


class CommentQueryHandler:
    def __init__(self, read_model: CommentReadModel, cache: RedisCache, ttl: int) -> None:
        self._rm = read_model
        self._cache = cache
        self._ttl = ttl

    def approved_for_post(self, post_id: str):
        return self._cache.get_or_load(
            CACHE_NS, RedisCache.make_key("post", post_id), self._ttl, lambda: self._rm.approved_for_post(post_id)
        )

    def admin_list(self, status: str | None, page: int, size: int):
        return self._rm.admin_list(status, page, size)

    def counts(self):
        return self._rm.counts()
