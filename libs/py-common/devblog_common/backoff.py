"""Yeniden bağlanma döngüleri için jitter'lı üstel geri çekilme."""

import random


class Backoff:
    """1s, 2s, 4s ... max_delay; başarıda sıfırlanır. Jitter, çok replikanın aynı anda saldırmasını önler."""

    def __init__(self, base: float = 1.0, max_delay: float = 30.0) -> None:
        self._base = base
        self._max = max_delay
        self.attempt = 0

    def next_delay(self) -> float:
        delay = min(self._max, self._base * (2**self.attempt))
        self.attempt += 1
        return delay * random.uniform(0.8, 1.2)  # noqa: S311  # nosec B311 - jitter, kriptografik değil

    def reset(self) -> None:
        self.attempt = 0
