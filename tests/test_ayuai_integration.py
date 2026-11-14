import pytest
from ayuai.providers.base import AIProvider, ProviderResponse
from ayuai.providers.provider_manager import ProviderManager
from ayuai.orchestrator import AYUAIOrchestrator

class StubProvider(AIProvider):
    def __init__(self, name, response):
        self.name, self.response = name, response
    async def analyze(self, prompt, system_prompt=None):
        return ProviderResponse(provider=self.name, model="stub", content=self.response, metadata={})

@pytest.mark.asyncio
async def test_end_to_end_pipeline_returns_decision():
    manager = ProviderManager()
    manager.register(StubProvider("a", "BUY. Trend is positive but risk remains."))
    manager.register(StubProvider("b", "BUY. Evidence supports buying cautiously."))
    result = await AYUAIOrchestrator(manager).analyze("Analyze BTC")
    assert result.stage == "final_decision"
    assert result.decision is not None
    assert result.decision.conclusion in {"BUY", "SELL", "WAIT", "HOLD", "AVOID", "INSUFFICIENT EVIDENCE"}
