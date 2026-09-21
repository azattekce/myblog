import redis


class RedisFixedWindowRateLimiter:
    def __init__(
        self, client: redis.Redis, limit: int, window_seconds: int, prefix: str = "ratelimit:comments"
    ) -> None:
        self._r, self._limit, self._window, self._prefix = client, limit, window_seconds, prefix

    def allow(self, key: str) -> bool:
        k = f"{self._prefix}:{key}"
        try:
            pipe = self._r.pipeline()
            pipe.incr(k)
            pipe.expire(k, self._window, nx=True)
            count, _ = pipe.execute()
            return int(count) <= self._limit
        except redis.RedisError:
            return True
