import pytest

from ayuai.debate.models import DebateReport
from ayuai.orchestrator import AYUAIOrchestrator
from ayuai.providers.base import ProviderResponse
from ayuai.providers.provider_manager import ProviderFailure, ProviderRun
from ayuai.reasoning.models import ReasoningReport


class FakeProviderManager:
    providers = ("openai", "anthropic", "gemini")

    async def analyze_all_detailed(self, prompt, *, system_prompt=None):
        return ProviderRun(
            responses=[
                ProviderResponse("openai", "fake-a", "CONCLUSION: WAIT"),
                ProviderResponse("anthropic", "fake-b", "CONCLUSION: WAIT"),
            ],
            failures=[
                ProviderFailure(
                    provider="gemini",
                    error="TimeoutError: provider request failed.",
                    category="timeout",
                    retryable=True,
                )
            ],
        )


@pytest.mark.asyncio
async def test_orchestrator_keeps_provider_failures_and_expected_count(monkeypatch):
    orchestrator = AYUAIOrchestrator(FakeProviderManager())

    monkeypatch.setattr(
        orchestrator.reasoning_engine,
        "analyze",
        lambda responses: ReasoningReport(),
    )

    async def fake_debate(question, analyses, reasoning):
        return DebateReport(status="completed")

    monkeypatch.setattr(orchestrator.debate_engine, "run", fake_debate)

    result = await orchestrator.analyze("Explain the test scenario.")

    assert result.expected_provider_count == 3
    assert len(result.analyses) == 2
    assert result.provider_failures[0]["provider"] == "gemini"
    assert result.decision.conclusion == "WAIT"
    assert result.decision.requires_human_review is True
    assert result.decision.confidence < 0.75
