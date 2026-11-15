"""Redis-backed fixed-window rate limiting for multi-process API deployments."""

from __future__ import annotations

import time
from typing import Protocol

from redis.asyncio import Redis
from redis.exceptions import RedisError

from .rate_limit import RateLimit


class RateLimitBackendUnavailable(RuntimeError):
    """Raised when the shared Redis rate-limit store cannot be reached."""


class RedisClient(Protocol):
    async def eval(self, script: str, numkeys: int, *keys_and_args): ...


class RedisRateLimiter:
    """Use an atomic Redis counter shared by every API process."""

    _INCREMENT_SCRIPT = """
    local count = redis.call('INCR', KEYS[1])
    if count == 1 then
        redis.call('EXPIRE', KEYS[1], ARGV[1])
    end
    return count
    """

    def __init__(
        self,
        redis_url: str,
        limit: RateLimit,
        client: RedisClient | None = None,
    ) -> None:
        self.limit = limit
        self.client = client or Redis.from_url(redis_url, decode_responses=True)

    async def check(self, key: str) -> tuple[bool, int]:
        now = int(time.time())
        window_id = now // self.limit.window_seconds
        redis_key = f"ayuai:rate-limit:{window_id}:{key}"
        retry_after = max(1, self.limit.window_seconds - (now % self.limit.window_seconds))

        try:
            count = int(
                await self.client.eval(
                    self._INCREMENT_SCRIPT,
                    1,
                    redis_key,
                    self.limit.window_seconds,
                )
            )
        except RedisError as exc:
            raise RateLimitBackendUnavailable("Redis rate-limit backend is unavailable.") from exc

        return count <= self.limit.requests, retry_after

    async def close(self) -> None:
        close = getattr(self.client, "aclose", None)
        if close is not None:
            await close()
