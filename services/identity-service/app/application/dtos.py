from dataclasses import dataclass
from datetime import datetime

from app.domain.user import User


@dataclass(frozen=True)
class UserDto:
    id: str
    username: str
    email: str
    display_name: str
    role: str
    last_login_at: datetime | None

    @classmethod
    def from_domain(cls, u: User) -> "UserDto":
        return cls(u.id, u.username, u.email, u.display_name, u.role.value, u.last_login_at)


@dataclass(frozen=True)
class AuthResult:
    access_token: str
    expires_in: int
    refresh_token: str
    refresh_expires_at: datetime
    user: UserDto
