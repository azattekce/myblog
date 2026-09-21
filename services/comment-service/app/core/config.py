from functools import lru_cache

from devblog_common.config import ServiceSettings


class Settings(ServiceSettings):
    service_name: str = "comment-service"
    db_name: str = "CommentDb"
    cache_ttl_seconds: int = 300
    comment_rate_limit: int = 5
    comment_rate_window_seconds: int = 600
    ip_hash_salt: str = "change-me-salt"


@lru_cache
def get_settings() -> Settings:
    return Settings()
