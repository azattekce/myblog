import contextlib
import logging

import redis

from devblog_common.web.security import REVOKED_JTI_KEY

log = logging.getLogger(__name__)


class RedisTokenRevocationStore:
    def __init__(self, client: redis.Redis) -> None:
        self._r = client

    def revoke_access_token(self, jti: str, ttl_seconds: int) -> None:
        try:
            self._r.set(REVOKED_JTI_KEY.format(jti=jti), "1", ex=ttl_seconds)
        except redis.RedisError:
            log.warning("Access token iptali Redis'e yazılamadı")


class RedisLoginThrottle:
    """Brute-force koruması: pencere içinde N başarısız deneme -> kilit."""

    def __init__(self, client: redis.Redis, max_attempts: int, window_minutes: int) -> None:
        self._r = client
        self._max = max_attempts
        self._window = window_minutes * 60

    @staticmethod
    def _key(key: str) -> str:
        return f"auth:login_fail:{key}"

    def is_locked(self, key: str) -> bool:
        try:
            return int(self._r.get(self._key(key)) or 0) >= self._max
        except redis.RedisError:
            return False

    def register_failure(self, key: str) -> None:
        try:
            pipe = self._r.pipeline()
            pipe.incr(self._key(key))
            pipe.expire(self._key(key), self._window)
            pipe.execute()
        except redis.RedisError:
            pass

    def reset(self, key: str) -> None:
        with contextlib.suppress(redis.RedisError):
            self._r.delete(self._key(key))
