"""Celery task entry points for AYUAI background intelligence."""
from __future__ import annotations
import asyncio
from celery import Celery

from ayuai.jobs.queue import REDIS_URL

celery_app = Celery("ayuai", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.task_track_started = True
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]


@celery_app.task(name="ayuai.health_check")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@celery_app.task(name="ayuai.analyze_question", bind=True)
def analyze_question(self, question: str, user_id: str) -> dict:
    """Run the AYUAI intelligence pipeline outside the API process."""
    clean_question = question.strip()
    if not clean_question:
        raise ValueError("A question or task is required.")

    self.update_state(state="STARTED", meta={"stage": "initializing"})

    async def run_pipeline() -> dict:
        from ayuai.bootstrap import build_provider_manager
        from ayuai.orchestrator import AYUAIOrchestrator

        manager = build_provider_manager()
        orchestrator = AYUAIOrchestrator(manager)
        result = await orchestrator.analyze(clean_question, user_id=user_id)
        decision = result.decision
        return {
            "status": "completed",
            "stage": result.stage,
            "question": result.question,
            "decision_id": result.decision_id,
            "decision": {
                "conclusion": decision.conclusion if decision else None,
                "confidence": decision.confidence if decision else None,
            },
            "provider_count": len(result.analyses),
        }

    self.update_state(
        state="ANALYZING",
        meta={"stage": "providers_reasoning_debate"},
    )
    return asyncio.run(run_pipeline())
