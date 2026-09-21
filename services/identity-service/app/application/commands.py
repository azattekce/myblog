from dataclasses import dataclass


@dataclass(frozen=True)
class LoginCommand:
    username: str
    password: str
    ip: str | None = None
    user_agent: str | None = None


@dataclass(frozen=True)
class RefreshCommand:
    refresh_token: str
    ip: str | None = None
    user_agent: str | None = None


@dataclass(frozen=True)
class LogoutCommand:
    refresh_token: str | None
    access_jti: str | None
    access_exp: int | None


@dataclass(frozen=True)
class SeedAdminCommand:
    username: str
    email: str
    display_name: str
    password: str


@dataclass(frozen=True)
class ChangePasswordCommand:
    user_id: str
    current_password: str
    new_password: str
