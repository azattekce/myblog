import redis


class RedisViewCounter:
    """Görüntülenme sayacı: yazma yoğun veri veritabanı yerine Redis'te (AOF ile kalıcı) tutulur."""

    def __init__(self, client: redis.Redis) -> None:
        self._r = client

    def hit(self, post_id: str) -> int:
        try:
            return int(self._r.incr(f"post:views:{post_id}"))
        except redis.RedisError:
            return 0
