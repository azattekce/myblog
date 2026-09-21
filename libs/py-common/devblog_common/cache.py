"""Distributed cache (Redis). Fail-open: Redis erişilemezse uygulama veritabanından çalışmaya devam eder.

Invalidation stratejisi: namespace versiyonlama. Bir namespace'e yazma olduğunda
sürüm INCR edilir; eski anahtarlar TTL ile kendiliğinden temizlenir (O(1), SCAN yok).
"""

import contextlib
import hashlib
import json
import logging
from collections.abc import Callable
from typing import Any

import redis

log = logging.getLogger(__name__)


def create_redis(url: str) -> redis.Redis:
    return redis.Redis.from_url(
        url,
        decode_responses=True,
        socket_timeout=2,
        socket_connect_timeout=2,
        health_check_interval=30,
        retry_on_timeout=True,
    )


class RedisCache:
    def __init__(self, client: redis.Redis, prefix: str) -> None:
        self._r = client
        self._prefix = prefix

    @staticmethod
    def make_key(*parts: Any) -> str:
        raw = json.dumps(parts, sort_keys=True, default=str, ensure_ascii=False)
        return hashlib.sha1(raw.encode(), usedforsecurity=False).hexdigest()[:20]  # yalnızca anahtar kısaltma

    def _version(self, namespace: str) -> int:
        try:
            return int(self._r.get(f"{self._prefix}:ns:{namespace}") or 0)
        except redis.RedisError:
            return -1

    def bump(self, namespace: str) -> None:
        try:
            self._r.incr(f"{self._prefix}:ns:{namespace}")
        except redis.RedisError:
            log.warning("Cache invalidation başarısız", extra={"namespace": namespace})

    def get_or_load(self, namespace: str, key: str, ttl: int, loader: Callable[[], Any]) -> Any:
        version = self._version(namespace)
        if version < 0:  # redis yok -> doğrudan kaynaktan
            return loader()
        full_key = f"{self._prefix}:{namespace}:v{version}:{key}"
        try:
            cached = self._r.get(full_key)
            if cached is not None:
                return json.loads(cached)
        except redis.RedisError:
            return loader()
        value = loader()
        with contextlib.suppress(redis.RedisError):
            self._r.set(full_key, json.dumps(value, ensure_ascii=False, default=str), ex=ttl)
        return value
