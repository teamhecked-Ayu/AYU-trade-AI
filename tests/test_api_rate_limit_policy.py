from fastapi import HTTPException
from starlette.requests import Request
import pytest

from api import main as api_main
from ayuai.security.rate_limit import RateLimit, RateLimiter


def request_for_ip(ip="192.0.2.10"):
    return Request({
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/test",
        "raw_path": b"/test",
        "query_string": b"",
        "headers": [],
        "client": (ip, 12345),
        "server": ("testserver", 80),
    })


@pytest.mark.asyncio
async def test_authenticated_api_polling_has_separate_higher_limit(monkeypatch):
    monkeypatch.setattr(api_main, "RATE_LIMIT_BACKEND", "memory")
    monkeypatch.setattr(api_main, "api_limiter", RateLimiter(RateLimit(120, 60)))
    monkeypatch.setattr(api_main, "auth_limiter", RateLimiter(RateLimit(2, 60)))
    request = request_for_ip()

    # Forty status requests in a minute is the dashboard's normal maximum.
    for _ in range(40):
        await api_main.enforce_rate_limit(request, scope="api")


@pytest.mark.asyncio
async def test_login_bucket_is_strict_and_separate_from_api_bucket(monkeypatch):
    monkeypatch.setattr(api_main, "RATE_LIMIT_BACKEND", "memory")
    monkeypatch.setattr(api_main, "auth_limiter", RateLimiter(RateLimit(2, 60)))
    monkeypatch.setattr(api_main, "api_limiter", RateLimiter(RateLimit(120, 60)))
    request = request_for_ip()

    await api_main.enforce_rate_limit(request, scope="auth")
    await api_main.enforce_rate_limit(request, scope="auth")
    with pytest.raises(HTTPException) as error:
        await api_main.enforce_rate_limit(request, scope="auth")
    assert error.value.status_code == 429

    # Exhausting login attempts must not consume the normal API allowance.
    for _ in range(40):
        await api_main.enforce_rate_limit(request, scope="api")


@pytest.mark.asyncio
async def test_different_ip_addresses_get_separate_api_buckets(monkeypatch):
    monkeypatch.setattr(api_main, "RATE_LIMIT_BACKEND", "memory")
    monkeypatch.setattr(api_main, "api_limiter", RateLimiter(RateLimit(1, 60)))

    await api_main.enforce_rate_limit(request_for_ip("192.0.2.10"))
    await api_main.enforce_rate_limit(request_for_ip("192.0.2.11"))
