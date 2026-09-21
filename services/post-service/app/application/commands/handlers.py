import logging
from collections.abc import Callable

from app.application.commands.models import CreateCategoryCommand, CreatePostCommand, UpdatePostCommand
from app.application.interfaces import CacheInvalidator, PostUnitOfWork
from app.domain.post import Category, Post
from devblog_common.domain import BusinessRuleViolation, ConflictError, NotFoundError

log = logging.getLogger(__name__)
CACHE_NS = "posts"


class PostCommandHandler:
    def __init__(self, uow_factory: Callable[[], PostUnitOfWork], cache: CacheInvalidator) -> None:
        self._uow = uow_factory
        self._cache = cache

    def _invalidate(self, uow: PostUnitOfWork) -> None:
        uow.on_commit(lambda: self._cache.bump(CACHE_NS))

    @staticmethod
    def _unique_slug(uow: PostUnitOfWork, base: str, exclude_id: str | None = None) -> str:
        slug, n = base, 2
        while uow.posts.slug_exists(slug, exclude_id):
            slug = f"{base}-{n}"
            n += 1
        return slug

    @staticmethod
    def _check_category(uow: PostUnitOfWork, category_id: str | None) -> None:
        if category_id and uow.categories.get(category_id) is None:
            raise BusinessRuleViolation("Kategori bulunamadı")

    def create(self, cmd: CreatePostCommand) -> str:
        with self._uow() as uow:
            self._check_category(uow, cmd.category_id)
            post = Post.create(
                title=cmd.title,
                summary=cmd.summary,
                content=cmd.content,
                author_id=cmd.author_id,
                author_name=cmd.author_name,
                slug=cmd.slug,
                category_id=cmd.category_id,
                tags=cmd.tags,
                cover_image_url=cmd.cover_image_url,
            )
            post.change_slug(self._unique_slug(uow, post.slug))
            if cmd.publish:
                post.publish()
            uow.posts.add(post)
            self._invalidate(uow)
            uow.commit()
            log.info("Yazı oluşturuldu", extra={"post_id": post.id, "published": post.is_published})
            return post.id

    def update(self, cmd: UpdatePostCommand) -> None:
        with self._uow() as uow:
            post = self._get(uow, cmd.post_id)
            self._check_category(uow, cmd.category_id)
            post.update(
                title=cmd.title,
                summary=cmd.summary,
                content=cmd.content,
                slug=cmd.slug,
                category_id=cmd.category_id,
                tags=cmd.tags,
                cover_image_url=cmd.cover_image_url,
            )
            if cmd.slug and uow.posts.slug_exists(post.slug, exclude_id=post.id):
                raise ConflictError("Bu slug başka bir yazıda kullanılıyor")
            uow.posts.update(post)
            self._invalidate(uow)
            uow.commit()

    def publish(self, post_id: str) -> None:
        with self._uow() as uow:
            post = self._get(uow, post_id)
            post.publish()
            uow.posts.update(post)
            self._invalidate(uow)
            uow.commit()

    def unpublish(self, post_id: str) -> None:
        with self._uow() as uow:
            post = self._get(uow, post_id)
            post.unpublish()
            uow.posts.update(post)
            self._invalidate(uow)
            uow.commit()

    def delete(self, post_id: str) -> None:
        with self._uow() as uow:
            post = self._get(uow, post_id)
            post.mark_deleted()
            uow.posts.delete(post)
            self._invalidate(uow)
            uow.commit()

    def sync_comment_count(self, post_id: str, count: int) -> None:
        """comment-service event'lerinden gelen sayıyı set eder (idempotent)."""
        with self._uow() as uow:
            post = uow.posts.get(post_id)
            if post is None:
                return
            post.sync_comment_count(count)
            uow.posts.update(post)
            self._invalidate(uow)
            uow.commit()

    def create_category(self, cmd: CreateCategoryCommand) -> str:
        with self._uow() as uow:
            category = Category.create(cmd.name, cmd.description, cmd.image_url)
            if uow.categories.slug_exists(category.slug):
                raise ConflictError("Bu isimde bir kategori zaten var")
            uow.categories.add(category)
            self._invalidate(uow)
            uow.commit()
            return category.id

    def delete_category(self, category_id: str) -> None:
        with self._uow() as uow:
            category = uow.categories.get(category_id)
            if category is None:
                raise NotFoundError("Kategori bulunamadı")
            if uow.categories.in_use(category_id):
                raise ConflictError("Kategoriye bağlı yazılar var")
            uow.categories.delete(category)
            self._invalidate(uow)
            uow.commit()

    @staticmethod
    def _get(uow: PostUnitOfWork, post_id: str) -> Post:
        post = uow.posts.get(post_id)
        if post is None:
            raise NotFoundError("Yazı bulunamadı")
        return post
