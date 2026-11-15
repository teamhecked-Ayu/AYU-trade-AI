"""AYUAI master controller with optional persistent decision recording."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from ayuai.agents.independent_analysis import IndependentAnalysisAgent
from ayuai.providers.provider_manager import ProviderManager
from ayuai.reasoning.reasoning_engine import ReasoningEngine
from ayuai.reasoning.models import ReasoningReport
from ayuai.debate.debate_engine import DebateEngine
from ayuai.debate.models import DebateReport
from ayuai.decision.decision_engine import DecisionEngine
from ayuai.decision.models import FinalDecision
from ayuai.database.repositories import DecisionRepository

@dataclass
class AnalysisResult:
    question: str
    analyses: list[dict[str, Any]]
    reasoning: ReasoningReport | None = None
    debate: DebateReport | None = None
    decision: FinalDecision | None = None
    decision_id: str | None = None
    stage: str = "independent_analysis"
    expected_provider_count: int = 0
    provider_failures: list[dict[str, Any]] = field(default_factory=list)

class AYUAIOrchestrator:
    def __init__(self, provider_manager: ProviderManager, session: AsyncSession | None = None) -> None:
        self.provider_manager = provider_manager
        self.session = session
        self.independent_agent = IndependentAnalysisAgent(provider_manager)
        self.reasoning_engine = ReasoningEngine()
        self.debate_engine = DebateEngine(provider_manager)
        self.decision_engine = DecisionEngine()

    async def analyze(self, question: str, user_id: str | None = None) -> AnalysisResult:
        question = question.strip()
        if not question:
            raise ValueError("A question or task is required.")
        provider_run = await self.independent_agent.run_detailed(question)
        if not provider_run.responses:
            raise RuntimeError("All configured AI providers failed.")

        responses = provider_run.responses
        expected_provider_count = len(self.provider_manager.providers)
        analyses = [
            {
                "provider": response.provider,
                "model": response.model,
                "content": response.content,
                "metadata": response.metadata,
            }
            for response in responses
        ]
        provider_failures = [
            {
                "provider": failure.provider,
                "error": failure.error,
                "category": failure.category,
                "retryable": failure.retryable,
            }
            for failure in provider_run.failures
        ]
        reasoning = self.reasoning_engine.analyze(responses)
        debate = await self.debate_engine.run(question, analyses, reasoning)
        decision = self.decision_engine.decide(
            analyses,
            reasoning,
            debate,
            expected_provider_count=expected_provider_count,
        )

        decision_id = None
        if self.session is not None and user_id:
            decision_id = str(uuid.uuid4())
            await DecisionRepository(self.session).create(
                id=decision_id, user_id=user_id, question=question,
                action=decision.conclusion, confidence=decision.confidence,
            )
            await self.session.commit()

        return AnalysisResult(
            question=question,
            analyses=analyses,
            reasoning=reasoning,
            debate=debate,
            decision=decision,
            decision_id=decision_id,
            stage="final_decision",
            expected_provider_count=expected_provider_count,
            provider_failures=provider_failures,
        )
