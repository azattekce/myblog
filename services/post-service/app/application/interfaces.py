from typing import Any, Protocol

from app.domain.repositories import CategoryRepository, PostRepository


class PostUnitOfWork(Protocol):
    posts: PostRepository
    categories: CategoryRepository

    def __enter__(self) -> "PostUnitOfWork": ...
    def __exit__(self, *args) -> None: ...
    def commit(self) -> None: ...
    def on_commit(self, callback) -> None: ...


class PostReadModel(Protocol):
    """CQRS okuma tarafı: domain nesnesi değil, doğrudan DTO (dict) döner."""

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
    ) -> dict[str, Any]: ...
    def get_by_slug(self, slug: str, published_only: bool) -> dict[str, Any] | None: ...
    def get_by_id(self, post_id: str) -> dict[str, Any] | None: ...
    def tags(self) -> list[dict[str, Any]]: ...
    def categories(self) -> list[dict[str, Any]]: ...
    def stats(self) -> dict[str, int]: ...


class CacheInvalidator(Protocol):
    def bump(self, namespace: str) -> None: ...
