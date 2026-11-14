import pytest

from ayuai.providers.base import AIProvider, ProviderResponse
from ayuai.providers.resilience import analyze_with_retry, classify_provider_error


class FlakyProvider(AIProvider):
    name = "flaky"

    def __init__(self):
        self.calls = 0

    async def analyze(self, prompt, *, system_prompt=None):
        self.calls += 1
        if self.calls == 1:
            raise TimeoutError("timed out")
        return ProviderResponse(self.name, "test", "ok")


class BadKeyProvider(AIProvider):
    name = "badkey"

    async def analyze(self, prompt, *, system_prompt=None):
        raise RuntimeError("API key authentication failed")


@pytest.mark.asyncio
async def test_retryable_timeout_recovers():
    provider = FlakyProvider()
    result = await analyze_with_retry(provider, "test", backoff_seconds=0)
    assert result.content == "ok"
    assert provider.calls == 2


@pytest.mark.asyncio
async def test_auth_failure_is_not_retried():
    provider = BadKeyProvider()
    with pytest.raises(RuntimeError):
        await analyze_with_retry(provider, "test", backoff_seconds=0)


def test_failure_categories():
    assert classify_provider_error("x", TimeoutError()).retryable is True
    assert classify_provider_error("x", RuntimeError("API key authentication failed")).retryable is False
