from abc import ABC, abstractmethod

from .comment import Comment, KnownPost


class CommentRepository(ABC):
    @abstractmethod
    def get(self, comment_id: str) -> Comment | None: ...

    @abstractmethod
    def add(self, comment: Comment) -> None: ...

    @abstractmethod
    def update(self, comment: Comment) -> None: ...

    @abstractmethod
    def delete(self, comment: Comment) -> None: ...

    @abstractmethod
    def count_approved(self, post_id: str) -> int: ...

    @abstractmethod
    def delete_for_post(self, post_id: str) -> int: ...


class KnownPostRepository(ABC):
    @abstractmethod
    def get(self, post_id: str) -> KnownPost | None: ...

    @abstractmethod
    def upsert(self, post: KnownPost) -> None: ...

    @abstractmethod
    def delete(self, post_id: str) -> None: ...
