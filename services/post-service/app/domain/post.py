from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from devblog_common.clock import to_iso_z, utcnow
from devblog_common.domain import AggregateRoot, BusinessRuleViolation, new_id

from .value_objects import normalize_tags, reading_time_minutes, slugify


class PostStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


@dataclass
class Post(AggregateRoot):
    id: str
    title: str
    slug: str
    summary: str
    content: str
    author_id: str
    author_name: str
    status: PostStatus = PostStatus.DRAFT
    category_id: str | None = None
    cover_image_url: str | None = None
    tags: list[str] = field(default_factory=list)
    reading_time: int = 1
    comment_count: int = 0
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    published_at: datetime | None = None

    # ------------------------------------------------------------ factory
    @classmethod
    def create(
        cls,
        *,
        title: str,
        summary: str,
        content: str,
        author_id: str,
        author_name: str,
        slug: str | None = None,
        category_id: str | None = None,
        tags: list[str] | None = None,
        cover_image_url: str | None = None,
    ) -> Post:
        cls._validate(title, summary, content)
        post = cls(
            id=new_id(),
            title=title.strip(),
            slug=slugify(slug or title),
            summary=summary.strip(),
            content=content,
            author_id=author_id,
            author_name=author_name,
            category_id=category_id,
            cover_image_url=cover_image_url,
            tags=normalize_tags(tags or []),
            reading_time=reading_time_minutes(content),
        )
        if not post.slug:
            raise BusinessRuleViolation("Başlıktan geçerli bir slug üretilemedi")
        post.record_event("post.created", post._payload())
        return post

    @staticmethod
    def _validate(title: str, summary: str, content: str) -> None:
        if not 3 <= len(title.strip()) <= 200:
            raise BusinessRuleViolation("Başlık 3-200 karakter olmalı")
        if len(summary.strip()) > 500:
            raise BusinessRuleViolation("Özet en fazla 500 karakter olabilir")
        if len(content.strip()) < 10:
            raise BusinessRuleViolation("İçerik en az 10 karakter olmalı")

    # ------------------------------------------------------------ behaviour
    @property
    def is_published(self) -> bool:
        return self.status == PostStatus.PUBLISHED

    def update(
        self,
        *,
        title: str,
        summary: str,
        content: str,
        slug: str | None,
        category_id: str | None,
        tags: list[str],
        cover_image_url: str | None,
    ) -> None:
        self._validate(title, summary, content)
        self.title, self.summary, self.content = title.strip(), summary.strip(), content
        if slug:
            self.slug = slugify(slug)
        self.category_id, self.cover_image_url = category_id, cover_image_url
        self.tags = normalize_tags(tags)
        self.reading_time = reading_time_minutes(content)
        self.updated_at = utcnow()
        self.record_event("post.updated", self._payload())

    def change_slug(self, slug: str) -> None:
        self.slug = slug

    def publish(self) -> None:
        if self.is_published:
            raise BusinessRuleViolation("Yazı zaten yayında")
        self.status = PostStatus.PUBLISHED
        self.published_at = self.published_at or utcnow()
        self.updated_at = utcnow()
        self.record_event("post.published", self._payload())

    def unpublish(self) -> None:
        if not self.is_published:
            raise BusinessRuleViolation("Yazı zaten taslak durumunda")
        self.status = PostStatus.DRAFT
        self.updated_at = utcnow()
        self.record_event("post.unpublished", self._payload())

    def mark_deleted(self) -> None:
        self.record_event("post.deleted", {"post_id": self.id, "slug": self.slug})

    def sync_comment_count(self, count: int) -> None:
        self.comment_count = max(0, count)

    def _payload(self) -> dict:
        return {
            "post_id": self.id,
            "slug": self.slug,
            "title": self.title,
            "status": self.status.value,
            "author_id": self.author_id,
            "tags": self.tags,
            "published_at": to_iso_z(self.published_at),
        }


@dataclass
class Category:
    id: str
    name: str
    slug: str
    description: str = ""
    image_url: str | None = None

    @classmethod
    def create(cls, name: str, description: str = "", image_url: str | None = None) -> Category:
        if not 2 <= len(name.strip()) <= 60:
            raise BusinessRuleViolation("Kategori adı 2-60 karakter olmalı")
        return cls(
            id=new_id(),
            name=name.strip(),
            slug=slugify(name, 80),
            description=description.strip()[:300],
            image_url=image_url,
        )
