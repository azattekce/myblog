"""Query tarafı: Redis cache-aside + read model. Command tarafından tamamen bağımsız."""

from typing import Any

from app.application.commands.handlers import CACHE_NS
from app.application.interfaces import PostReadModel
from devblog_common.cache import RedisCache
from devblog_common.domain import NotFoundError


class PostQueryHandler:
    def __init__(self, read_model: PostReadModel, cache: RedisCache, ttl: int, view_counter=None) -> None:
        self._rm = read_model
        self._cache = cache
        self._ttl = ttl
        self._views = view_counter

    def list_published(self, page: int, size: int, tag: str | None, category: str | None, q: str | None):
        key = RedisCache.make_key("list", page, size, tag, category, q)
        return self._cache.get_or_load(
            CACHE_NS,
            key,
            self._ttl,
            lambda: self._rm.list_posts(
                page=page, size=size, published_only=True, status=None, tag=tag, category=category, q=q
            ),
        )

    def get_published(self, slug: str) -> dict[str, Any]:
        post = self._cache.get_or_load(
            CACHE_NS, RedisCache.make_key("slug", slug), self._ttl, lambda: self._rm.get_by_slug(slug, True)
        )
        if post is None:
            raise NotFoundError("Yazı bulunamadı")
        post = dict(post)
        post["view_count"] = self._views.hit(post["id"]) if self._views else 0
        return post

    def tags(self):
        return self._cache.get_or_load(CACHE_NS, "tags", self._ttl, self._rm.tags)

    def categories(self):
        return self._cache.get_or_load(CACHE_NS, "categories", self._ttl, self._rm.categories)

    # ---- admin (cache yok: her zaman güncel)
    def admin_list(self, page: int, size: int, status: str | None, q: str | None):
        return self._rm.list_posts(
            page=page, size=size, published_only=False, status=status, tag=None, category=None, q=q
        )

    def admin_get(self, post_id: str) -> dict[str, Any]:
        post = self._rm.get_by_id(post_id)
        if post is None:
            raise NotFoundError("Yazı bulunamadı")
        return post

    def stats(self) -> dict[str, int]:
        return self._rm.stats()
