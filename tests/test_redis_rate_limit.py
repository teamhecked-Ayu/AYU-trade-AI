import pytest
from redis.exceptions import RedisError

from ayuai.security.rate_limit import RateLimit
from ayuai.security.redis_rate_limit import (
    RateLimitBackendUnavailable,
    RedisRateLimiter,
)


class FakeRedis:
    def __init__(self, fail=False):
        self.count = 0
        self.fail = fail
        self.calls = []

    async def eval(self, script, numkeys, key, window):
        self.calls.append((script, numkeys, key, window))
        if self.fail:
            raise RedisError("connection failed")
        self.count += 1
        return self.count

    async def aclose(self):
        return None


@pytest.mark.asyncio
async def test_redis_rate_limiter_shares_a_fixed_window_counter(monkeypatch):
    monkeypatch.setattr("ayuai.security.redis_rate_limit.time.time", lambda: 125)
    client = FakeRedis()
    limiter = RedisRateLimiter(
        "redis://unused",
        RateLimit(requests=2, window_seconds=60),
        client=client,
    )

    assert await limiter.check("192.0.2.10") == (True, 55)
    assert await limiter.check("192.0.2.10") == (True, 55)
    assert await limiter.check("192.0.2.10") == (False, 55)
    assert client.calls[0][2] == "ayuai:rate-limit:2:192.0.2.10"
    assert client.calls[0][3] == 60


@pytest.mark.asyncio
async def test_redis_rate_limiter_fails_closed_when_redis_is_unavailable():
    limiter = RedisRateLimiter(
        "redis://unused",
        RateLimit(requests=2, window_seconds=60),
        client=FakeRedis(fail=True),
    )

    with pytest.raises(RateLimitBackendUnavailable):
        await limiter.check("192.0.2.10")


@pytest.mark.asyncio
async def test_auth_and_api_scopes_use_separate_redis_keys(monkeypatch):
    monkeypatch.setattr("ayuai.security.redis_rate_limit.time.time", lambda: 125)
    client = FakeRedis()
    auth = RedisRateLimiter(
        "redis://unused",
        RateLimit(requests=2, window_seconds=60),
        client=client,
    )
    api = RedisRateLimiter(
        "redis://unused",
        RateLimit(requests=120, window_seconds=60),
        client=client,
    )

    await auth.check("auth:192.0.2.10")
    await api.check("api:192.0.2.10")

    assert client.calls[0][2] != client.calls[1][2]
    assert client.calls[0][2].endswith("auth:192.0.2.10")
    assert client.calls[1][2].endswith("api:192.0.2.10")


@pytest.mark.asyncio
async def test_paper_requests_use_a_separate_redis_bucket():
    client = FakeRedis()
    paper = RedisRateLimiter(
        "redis://unused",
        RateLimit(requests=60, window_seconds=60),
        client=client,
    )
    api = RedisRateLimiter(
        "redis://unused",
        RateLimit(requests=120, window_seconds=60),
        client=client,
    )

    await paper.check("paper:192.0.2.10")
    await api.check("api:192.0.2.10")

    assert client.calls[0][2] != client.calls[1][2]
    assert client.calls[0][2].endswith("paper:192.0.2.10")
    assert client.calls[1][2].endswith("api:192.0.2.10")
