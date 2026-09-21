"""CQRS Query tarafı: optimize edilmiş, projeksiyon odaklı okuma sorguları."""

import math
from typing import Any

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import sessionmaker

from devblog_common.clock import to_iso_z

from .models import CategoryModel, PostModel, PostTagModel

_SUMMARY_COLS = (
    PostModel.id,
    PostModel.title,
    PostModel.slug,
    PostModel.summary,
    PostModel.status,
    PostModel.author_name,
    PostModel.cover_image_url,
    PostModel.reading_time,
    PostModel.comment_count,
    PostModel.created_at,
    PostModel.updated_at,
    PostModel.published_at,
    PostModel.category_id,
    CategoryModel.name.label("category_name"),
    CategoryModel.slug.label("category_slug"),
)


class SqlAlchemyPostReadModel:
    def __init__(self, session_factory: sessionmaker) -> None:
        self._sf = session_factory

    def _tags_for(self, session, ids: list[str]) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {i: [] for i in ids}
        if ids:
            rows = session.execute(
                select(PostTagModel.post_id, PostTagModel.tag).where(PostTagModel.post_id.in_(ids))
            ).all()
            for post_id, tag in rows:
                result[post_id].append(tag)
        return {k: sorted(v) for k, v in result.items()}

    @staticmethod
    def _summary(row, tags: list[str]) -> dict[str, Any]:
        return {
            "id": row.id,
            "title": row.title,
            "slug": row.slug,
            "summary": row.summary,
            "status": row.status,
            "author_name": row.author_name,
            "cover_image_url": row.cover_image_url,
            "reading_time": row.reading_time,
            "comment_count": row.comment_count,
            "tags": tags,
            "category": {"id": row.category_id, "name": row.category_name, "slug": row.category_slug}
            if row.category_id
            else None,
            "created_at": to_iso_z(row.created_at),
            "updated_at": to_iso_z(row.updated_at),
            "published_at": to_iso_z(row.published_at),
        }

    def list_posts(
        self,
        *,
        page: int,
        size: int,
        published_only: bool,
        status: str | None,
        tag: str | None,
        category: str | None,
        q: str | None,
    ) -> dict[str, Any]:
        filters = []
        if published_only:
            filters.append(PostModel.status == "published")
        elif status:
            filters.append(PostModel.status == status)
        if tag:
            filters.append(PostModel.id.in_(select(PostTagModel.post_id).where(PostTagModel.tag == tag)))
        if category:
            filters.append(CategoryModel.slug == category)
        if q:
            like = f"%{q.strip()[:100]}%"
            filters.append(or_(PostModel.title.ilike(like), PostModel.summary.ilike(like)))

        base = select(*_SUMMARY_COLS).outerjoin(CategoryModel, CategoryModel.id == PostModel.category_id)
        count_q = (
            select(func.count())
            .select_from(PostModel)
            .outerjoin(CategoryModel, CategoryModel.id == PostModel.category_id)
        )
        for f in filters:
            base = base.where(f)
            count_q = count_q.where(f)

        order = (
            (PostModel.published_at.desc(), PostModel.id)
            if published_only
            else (PostModel.updated_at.desc(), PostModel.id)
        )
        with self._sf() as s:
            total = s.execute(count_q).scalar_one()
            rows = s.execute(base.order_by(*order).offset((page - 1) * size).limit(size)).all()
            tags = self._tags_for(s, [r.id for r in rows])
        return {
            "items": [self._summary(r, tags[r.id]) for r in rows],
            "page": page,
            "size": size,
            "total": total,
            "pages": max(1, math.ceil(total / size)),
        }

    def _detail(self, where) -> dict[str, Any] | None:
        q = (
            select(*_SUMMARY_COLS, PostModel.content)
            .outerjoin(CategoryModel, CategoryModel.id == PostModel.category_id)
            .where(*where)
        )
        with self._sf() as s:
            row = s.execute(q).first()
            if row is None:
                return None
            data = self._summary(row, self._tags_for(s, [row.id])[row.id])
        data["content"] = row.content
        return data

    def get_by_slug(self, slug: str, published_only: bool) -> dict[str, Any] | None:
        where = [PostModel.slug == slug]
        if published_only:
            where.append(PostModel.status == "published")
        return self._detail(where)

    def get_by_id(self, post_id: str) -> dict[str, Any] | None:
        return self._detail([PostModel.id == post_id])

    def tags(self) -> list[dict[str, Any]]:
        q = (
            select(PostTagModel.tag, func.count().label("count"))
            .join(PostModel, PostModel.id == PostTagModel.post_id)
            .where(PostModel.status == "published")
            .group_by(PostTagModel.tag)
            .order_by(func.count().desc(), PostTagModel.tag)
        )
        with self._sf() as s:
            return [{"tag": t, "count": c} for t, c in s.execute(q).all()]

    def categories(self) -> list[dict[str, Any]]:
        published = func.sum(case((PostModel.status == "published", 1), else_=0))
        q = (
            select(
                CategoryModel.id,
                CategoryModel.name,
                CategoryModel.slug,
                CategoryModel.description,
                CategoryModel.image_url,
                func.coalesce(published, 0).label("post_count"),
            )
            .outerjoin(PostModel, PostModel.category_id == CategoryModel.id)
            .group_by(
                CategoryModel.id, CategoryModel.name, CategoryModel.slug, CategoryModel.description, CategoryModel.image_url
            )
            .order_by(CategoryModel.name)
        )
        with self._sf() as s:
            return [
                {
                    "id": r.id,
                    "name": r.name,
                    "slug": r.slug,
                    "description": r.description,
                    "image_url": r.image_url,
                    "post_count": int(r.post_count or 0),
                }
                for r in s.execute(q).all()
            ]

    def stats(self) -> dict[str, int]:
        q = select(
            func.count().label("total"),
            func.coalesce(func.sum(case((PostModel.status == "published", 1), else_=0)), 0).label("published"),
            func.coalesce(func.sum(PostModel.comment_count), 0).label("comments"),
        )
        with self._sf() as s:
            r = s.execute(q).one()
        return {
            "total": int(r.total),
            "published": int(r.published),
            "drafts": int(r.total) - int(r.published),
            "comments": int(r.comments),
        }
