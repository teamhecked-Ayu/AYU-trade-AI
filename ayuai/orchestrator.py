"""AYUAI master controller."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from ayuai.agents.independent_analysis import IndependentAnalysisAgent
from ayuai.providers.provider_manager import ProviderManager
from ayuai.reasoning.reasoning_engine import ReasoningEngine
from ayuai.reasoning.models import ReasoningReport
from ayuai.debate.debate_engine import DebateEngine
from ayuai.debate.models import DebateReport
from ayuai.decision.decision_engine import DecisionEngine
from ayuai.decision.models import FinalDecision

@dataclass
class AnalysisResult:
    question: str
    analyses: list[dict[str, Any]]
    reasoning: ReasoningReport | None = None
    debate: DebateReport | None = None
    decision: FinalDecision | None = None
    stage: str = "independent_analysis"

class AYUAIOrchestrator:
    def __init__(self, provider_manager: ProviderManager) -> None:
        self.provider_manager = provider_manager
        self.independent_agent = IndependentAnalysisAgent(provider_manager)
        self.reasoning_engine = ReasoningEngine()
        self.debate_engine = DebateEngine(provider_manager)
        self.decision_engine = DecisionEngine()

    async def analyze(self, question: str) -> AnalysisResult:
        question = question.strip()
        if not question:
            raise ValueError("A question or task is required.")

        responses = await self.independent_agent.run(question)
        analyses = [
            {"provider": r.provider, "model": r.model, "content": r.content, "metadata": r.metadata}
            for r in responses
        ]
        reasoning = self.reasoning_engine.analyze(responses)
        debate = await self.debate_engine.run(question, analyses, reasoning)
        decision = self.decision_engine.decide(analyses, reasoning, debate)

        return AnalysisResult(
            question=question,
            analyses=analyses,
            reasoning=reasoning,
            debate=debate,
            decision=decision,
            stage="final_decision",
        )
