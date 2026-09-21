from sqlalchemy import Boolean, DateTime, Index, String, Unicode
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from devblog_common.persistence import build_outbox_model


class Base(DeclarativeBase):
    pass


class CommentModel(Base):
    __tablename__ = "comments"
    __table_args__ = (Index("ix_comments_post_status", "post_id", "status"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    post_id: Mapped[str] = mapped_column(String(36), nullable=False)
    author_name: Mapped[str] = mapped_column(Unicode(60), nullable=False)
    author_email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    content: Mapped[str] = mapped_column(Unicode(2000), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at = mapped_column(DateTime, nullable=False)
    moderated_at = mapped_column(DateTime, nullable=True)


class KnownPostModel(Base):
    __tablename__ = "known_posts"

    post_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False)


OutboxMessage = build_outbox_model(Base)
