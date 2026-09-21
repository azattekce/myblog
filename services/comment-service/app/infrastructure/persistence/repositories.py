import math
from collections.abc import Callable
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.domain.comment import Comment, CommentStatus, KnownPost
from app.domain.repositories import CommentRepository, KnownPostRepository
from devblog_common.clock import to_iso_z

from .models import CommentModel, KnownPostModel


class SqlAlchemyCommentRepository(CommentRepository):
    def __init__(self, session: Session, track: Callable) -> None:
        self._s = session
        self._track = track

    def get(self, comment_id: str) -> Comment | None:
        m = self._s.get(CommentModel, comment_id)
        if m is None:
            return None
        c = Comment(
            id=m.id,
            post_id=m.post_id,
            author_name=m.author_name,
            content=m.content,
            author_email=m.author_email,
            status=CommentStatus(m.status),
            ip_hash=m.ip_hash,
            created_at=m.created_at,
            moderated_at=m.moderated_at,
        )
        self._track(c)
        return c

    def add(self, c: Comment) -> None:
        self._s.add(
            CommentModel(
                id=c.id,
                post_id=c.post_id,
                author_name=c.author_name,
                author_email=c.author_email,
                content=c.content,
                status=c.status.value,
                ip_hash=c.ip_hash,
                created_at=c.created_at,
                moderated_at=c.moderated_at,
            )
        )
        self._track(c)

    def update(self, c: Comment) -> None:
        m = self._s.get(CommentModel, c.id)
        m.status, m.moderated_at = c.status.value, c.moderated_at
        self._track(c)

    def delete(self, c: Comment) -> None:
        self._s.execute(delete(CommentModel).where(CommentModel.id == c.id))
        self._track(c)

    def count_approved(self, post_id: str) -> int:
        q = (
            select(func.count())
            .select_from(CommentModel)
            .where(CommentModel.post_id == post_id, CommentModel.status == "approved")
        )
        return int(self._s.execute(q).scalar_one())

    def delete_for_post(self, post_id: str) -> int:
        return self._s.execute(delete(CommentModel).where(CommentModel.post_id == post_id)).rowcount or 0


class SqlAlchemyKnownPostRepository(KnownPostRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def get(self, post_id: str) -> KnownPost | None:
        m = self._s.get(KnownPostModel, post_id)
        return KnownPost(m.post_id, m.slug, m.title, m.is_published) if m else None

    def upsert(self, post: KnownPost) -> None:
        m = self._s.get(KnownPostModel, post.post_id)
        if m is None:
            self._s.add(
                KnownPostModel(post_id=post.post_id, slug=post.slug, title=post.title, is_published=post.is_published)
            )
        else:
            m.slug, m.title, m.is_published = post.slug, post.title, post.is_published

    def delete(self, post_id: str) -> None:
        self._s.execute(delete(KnownPostModel).where(KnownPostModel.post_id == post_id))


class SqlAlchemyCommentReadModel:
    def __init__(self, sf: sessionmaker) -> None:
        self._sf = sf

    def approved_for_post(self, post_id: str) -> list[dict[str, Any]]:
        q = (
            select(CommentModel.id, CommentModel.author_name, CommentModel.content, CommentModel.created_at)
            .where(CommentModel.post_id == post_id, CommentModel.status == "approved")
            .order_by(CommentModel.created_at, CommentModel.id)
        )
        with self._sf() as s:
            return [
                {"id": r.id, "author_name": r.author_name, "content": r.content, "created_at": to_iso_z(r.created_at)}
                for r in s.execute(q).all()
            ]

    def admin_list(self, status: str | None, page: int, size: int) -> dict[str, Any]:
        base = select(CommentModel, KnownPostModel.title, KnownPostModel.slug).outerjoin(
            KnownPostModel, KnownPostModel.post_id == CommentModel.post_id
        )
        count_q = select(func.count()).select_from(CommentModel)
        if status:
            base = base.where(CommentModel.status == status)
            count_q = count_q.where(CommentModel.status == status)
        with self._sf() as s:
            total = s.execute(count_q).scalar_one()
            rows = s.execute(
                base.order_by(CommentModel.created_at.desc(), CommentModel.id).offset((page - 1) * size).limit(size)
            ).all()
            items = [
                {
                    "id": c.id,
                    "post_id": c.post_id,
                    "post_title": title,
                    "post_slug": slug,
                    "author_name": c.author_name,
                    "author_email": c.author_email,
                    "content": c.content,
                    "status": c.status,
                    "created_at": to_iso_z(c.created_at),
                }
                for c, title, slug in rows
            ]
        return {"items": items, "page": page, "size": size, "total": total, "pages": max(1, math.ceil(total / size))}

    def counts(self) -> dict[str, int]:
        q = select(CommentModel.status, func.count()).group_by(CommentModel.status)
        with self._sf() as s:
            data = {st: int(n) for st, n in s.execute(q).all()}
        return {k: data.get(k, 0) for k in ("pending", "approved", "rejected")}
