from collections.abc import Callable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domain.post import Category, Post, PostStatus
from app.domain.repositories import CategoryRepository, PostRepository

from .models import CategoryModel, PostModel, PostTagModel


class SqlAlchemyPostRepository(PostRepository):
    def __init__(self, session: Session, track: Callable) -> None:
        self._s = session
        self._track = track

    def get(self, post_id: str) -> Post | None:
        m = self._s.get(PostModel, post_id)
        if m is None:
            return None
        tags = self._s.execute(select(PostTagModel.tag).where(PostTagModel.post_id == post_id)).scalars().all()
        post = Post(
            id=m.id,
            title=m.title,
            slug=m.slug,
            summary=m.summary,
            content=m.content,
            author_id=m.author_id,
            author_name=m.author_name,
            status=PostStatus(m.status),
            category_id=m.category_id,
            cover_image_url=m.cover_image_url,
            tags=sorted(tags),
            reading_time=m.reading_time,
            comment_count=m.comment_count,
            created_at=m.created_at,
            updated_at=m.updated_at,
            published_at=m.published_at,
        )
        self._track(post)
        return post

    def slug_exists(self, slug: str, exclude_id: str | None = None) -> bool:
        q = select(PostModel.id).where(PostModel.slug == slug)
        if exclude_id:
            q = q.where(PostModel.id != exclude_id)
        return self._s.execute(q).first() is not None

    def add(self, post: Post) -> None:
        self._s.add(PostModel(id=post.id, created_at=post.created_at, **self._fields(post)))
        self._s.flush()
        self._replace_tags(post)
        self._track(post)

    def update(self, post: Post) -> None:
        m = self._s.get(PostModel, post.id)
        for key, value in self._fields(post).items():
            setattr(m, key, value)
        self._replace_tags(post)
        self._track(post)

    def delete(self, post: Post) -> None:
        self._s.execute(delete(PostTagModel).where(PostTagModel.post_id == post.id))
        self._s.execute(delete(PostModel).where(PostModel.id == post.id))
        self._track(post)

    def _replace_tags(self, post: Post) -> None:
        self._s.execute(delete(PostTagModel).where(PostTagModel.post_id == post.id))
        for tag in post.tags:
            self._s.add(PostTagModel(post_id=post.id, tag=tag))

    @staticmethod
    def _fields(p: Post) -> dict:
        return {
            "title": p.title,
            "slug": p.slug,
            "summary": p.summary,
            "content": p.content,
            "status": p.status.value,
            "author_id": p.author_id,
            "author_name": p.author_name,
            "category_id": p.category_id,
            "cover_image_url": p.cover_image_url,
            "reading_time": p.reading_time,
            "comment_count": p.comment_count,
            "updated_at": p.updated_at,
            "published_at": p.published_at,
        }


class SqlAlchemyCategoryRepository(CategoryRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def get(self, category_id: str) -> Category | None:
        m = self._s.get(CategoryModel, category_id)
        return Category(m.id, m.name, m.slug, m.description, m.image_url) if m else None

    def slug_exists(self, slug: str) -> bool:
        return self._s.execute(select(CategoryModel.id).where(CategoryModel.slug == slug)).first() is not None

    def add(self, category: Category) -> None:
        self._s.add(
            CategoryModel(
                id=category.id,
                name=category.name,
                slug=category.slug,
                description=category.description,
                image_url=category.image_url,
            )
        )

    def delete(self, category: Category) -> None:
        self._s.execute(delete(CategoryModel).where(CategoryModel.id == category.id))

    def in_use(self, category_id: str) -> bool:
        return self._s.execute(select(PostModel.id).where(PostModel.category_id == category_id)).first() is not None
