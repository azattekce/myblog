from functools import lru_cache

from devblog_common.config import ServiceSettings


class Settings(ServiceSettings):
    service_name: str = "post-service"
    db_name: str = "PostDb"
    cache_ttl_seconds: int = 300


@lru_cache
def get_settings() -> Settings:
    return Settings()
