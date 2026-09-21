"""Repository soyutlamaları (port). Implementasyon infrastructure katmanındadır."""

from abc import ABC, abstractmethod

from .refresh_token import RefreshToken
from .user import User


class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: str) -> User | None: ...

    @abstractmethod
    def get_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    def exists(self, username: str, email: str) -> bool: ...

    @abstractmethod
    def add(self, user: User) -> None: ...

    @abstractmethod
    def update(self, user: User) -> None: ...


class RefreshTokenRepository(ABC):
    @abstractmethod
    def get_by_hash(self, token_hash: str) -> RefreshToken | None: ...

    @abstractmethod
    def add(self, token: RefreshToken) -> None: ...

    @abstractmethod
    def update(self, token: RefreshToken) -> None: ...

    @abstractmethod
    def revoke_family(self, family_id: str) -> int: ...
