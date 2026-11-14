import asyncio
import pytest

from ayuai.providers.base import AIProvider, ProviderResponse
from ayuai.providers.provider_manager import ProviderManager


class GoodProvider(AIProvider):
    name = "good"
    async def analyze(self, prompt, *, system_prompt=None):
        return ProviderResponse(self.name, "test", "ok")


class FailingProvider(AIProvider):
    name = "failing"
    async def analyze(self, prompt, *, system_prompt=None):
        raise RuntimeError("secret-key-must-not-leak")


class SlowProvider(AIProvider):
    name = "slow"
    async def analyze(self, prompt, *, system_prompt=None):
        await asyncio.sleep(1)
        return ProviderResponse(self.name, "test", "late")


@pytest.mark.asyncio
async def test_partial_provider_failure_does_not_stop_analysis():
    manager = ProviderManager(timeout_seconds=1)
    manager.register(GoodProvider())
    manager.register(FailingProvider())

    run = await manager.analyze_all_detailed("test")

    assert len(run.responses) == 1
    assert run.responses[0].provider == "good"
    assert len(run.failures) == 1
    assert "secret-key" not in run.failures[0].error


@pytest.mark.asyncio
async def test_provider_timeout_is_isolated():
    manager = ProviderManager(timeout_seconds=0.01)
    manager.register(GoodProvider())
    manager.register(SlowProvider())

    run = await manager.analyze_all_detailed("test")

    assert [response.provider for response in run.responses] == ["good"]
    assert run.failures[0].provider == "slow"
    assert run.failures[0].error == "Provider request timed out."


@pytest.mark.asyncio
async def test_all_failures_do_not_expose_raw_provider_errors():
    manager = ProviderManager(timeout_seconds=1)
    manager.register(FailingProvider())

    with pytest.raises(RuntimeError, match="All AI providers failed"):
        await manager.analyze_all("test")
