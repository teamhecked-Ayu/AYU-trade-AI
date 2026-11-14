from ayuai.security.rate_limit import RateLimit, RateLimiter


def test_rate_limit_blocks_after_limit():
    limiter = RateLimiter(RateLimit(requests=2, window_seconds=60))
    assert limiter.check("user")[0] is True
    assert limiter.check("user")[0] is True
    allowed, retry_after = limiter.check("user")
    assert allowed is False
    assert retry_after >= 1
