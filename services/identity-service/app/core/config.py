from functools import lru_cache

from devblog_common.config import ServiceSettings


class Settings(ServiceSettings):
    service_name: str = "identity-service"
    db_name: str = "IdentityDb"

    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7

    admin_username: str = "admin"
    admin_email: str = "admin@devblog.local"
    admin_display_name: str = "Blog Yazarı"
    admin_password: str = "Admin123!"

    cookie_secure: bool = False
    cookie_samesite: str = "strict"
    refresh_cookie_name: str = "devblog_rt"
    refresh_cookie_path: str = "/api/identity/auth"

    login_max_attempts: int = 5
    login_lock_minutes: int = 15


@lru_cache
def get_settings() -> Settings:
    return Settings()
