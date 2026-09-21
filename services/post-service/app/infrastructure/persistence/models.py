from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Unicode, UnicodeText
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from devblog_common.persistence import build_outbox_model


class Base(DeclarativeBase):
    pass


class CategoryModel(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(Unicode(60), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Unicode(300), nullable=False, default="")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)


class PostModel(Base):
    __tablename__ = "posts"
    __table_args__ = (Index("ix_posts_status_published_at", "status", "published_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    summary: Mapped[str] = mapped_column(Unicode(500), nullable=False, default="")
    content: Mapped[str] = mapped_column(UnicodeText, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    author_id: Mapped[str] = mapped_column(String(36), nullable=False)
    author_name: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    category_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("categories.id"), nullable=True, index=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reading_time: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at = mapped_column(DateTime, nullable=False)
    updated_at = mapped_column(DateTime, nullable=False)
    published_at = mapped_column(DateTime, nullable=True)


class PostTagModel(Base):
    __tablename__ = "post_tags"

    post_id: Mapped[str] = mapped_column(String(36), ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    tag: Mapped[str] = mapped_column(String(30), primary_key=True, index=True)


OutboxMessage = build_outbox_model(Base)
