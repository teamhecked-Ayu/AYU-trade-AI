"""AYUAI master controller."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from ayuai.agents.independent_analysis import IndependentAnalysisAgent
from ayuai.providers.provider_manager import ProviderManager
from ayuai.reasoning.reasoning_engine import ReasoningEngine
from ayuai.reasoning.models import ReasoningReport

@dataclass
class AnalysisResult:
    question: str
    analyses: list[dict[str, Any]]
    reasoning: ReasoningReport | None = None
    stage: str = "independent_analysis"

class AYUAIOrchestrator:
    def __init__(self, provider_manager: ProviderManager) -> None:
        self.provider_manager = provider_manager
        self.independent_agent = IndependentAnalysisAgent(provider_manager)
        self.reasoning_engine = ReasoningEngine()

    async def analyze(self, question: str) -> AnalysisResult:
        question = question.strip()
        if not question:
            raise ValueError("A question or task is required.")
        responses = await self.independent_agent.run(question)
        reasoning = self.reasoning_engine.analyze(responses)
        return AnalysisResult(
            question=question,
            analyses=[
                {"provider": r.provider, "model": r.model, "content": r.content, "metadata": r.metadata}
                for r in responses
            ],
            reasoning=reasoning,
            stage="structured_reasoning",
        )
