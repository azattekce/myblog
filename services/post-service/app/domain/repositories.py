from abc import ABC, abstractmethod

from .post import Category, Post


class PostRepository(ABC):
    @abstractmethod
    def get(self, post_id: str) -> Post | None: ...

    @abstractmethod
    def slug_exists(self, slug: str, exclude_id: str | None = None) -> bool: ...

    @abstractmethod
    def add(self, post: Post) -> None: ...

    @abstractmethod
    def update(self, post: Post) -> None: ...

    @abstractmethod
    def delete(self, post: Post) -> None: ...


class CategoryRepository(ABC):
    @abstractmethod
    def get(self, category_id: str) -> Category | None: ...

    @abstractmethod
    def slug_exists(self, slug: str) -> bool: ...

    @abstractmethod
    def add(self, category: Category) -> None: ...

    @abstractmethod
    def delete(self, category: Category) -> None: ...

    @abstractmethod
    def in_use(self, category_id: str) -> bool: ...
