"""Small dependency-free rate limiter for the AYUAI API.

This is process-local and intended for a single API instance. Production multi-instance
deployments should replace the storage backend with Redis.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class RateLimit:
    requests: int
    window_seconds: int


class RateLimiter:
    def __init__(self, limit: RateLimit) -> None:
        self.limit = limit
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> tuple[bool, int]:
        now = time.monotonic()
        cutoff = now - self.limit.window_seconds
        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= self.limit.requests:
                retry_after = max(1, int(self.limit.window_seconds - (now - bucket[0])))
                return False, retry_after
            bucket.append(now)
            return True, 0
