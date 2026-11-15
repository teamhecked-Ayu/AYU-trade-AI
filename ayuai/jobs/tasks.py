"""Celery task entry points for AYUAI background intelligence."""

from __future__ import annotations

import asyncio
import uuid

from celery import Celery

from ayuai.jobs.queue import REDIS_URL

celery_app = Celery("ayuai", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.task_track_started = True
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]


@celery_app.task(name="ayuai.health_check")
def health_check():
    return {"status": "ok"}


async def persist_decision(result, user_id: str) -> str | None:
    """Persist a completed analysis decision in the user's database history."""
    if result.decision is None:
        return None

    from ayuai.database.connection import session_scope
    from ayuai.database.repositories import DecisionRepository

    decision_id = str(uuid.uuid4())
    async with session_scope() as session:
        await DecisionRepository(session).create(
            id=decision_id,
            user_id=user_id,
            question=result.question,
            action=result.decision.conclusion,
            confidence=result.decision.confidence,
        )

    result.decision_id = decision_id
    return decision_id


@celery_app.task(name="ayuai.analyze_question", bind=True)
def analyze_question(self, question: str, user_id: str) -> dict:
    clean_question = question.strip()
    if not clean_question:
        raise ValueError("A question or task is required.")

    self.update_state(state="STARTED", meta={"stage": "loading_user_providers"})

    async def run_pipeline():
        from ayuai.database.connection import session_scope
        from ayuai.database.repositories_credentials import ProviderCredentialRepository
        from ayuai.security.key_vault import KeyVault
        from ayuai.bootstrap import build_provider_manager
        from ayuai.orchestrator import AYUAIOrchestrator

        async with session_scope() as session:
            keys = await ProviderCredentialRepository(session, KeyVault()).get_decrypted(user_id)

        self.update_state(
            state="ANALYZING",
            meta={"stage": "providers_reasoning_debate", "provider_count": len(keys)},
        )
        manager = build_provider_manager(keys)
        result = await AYUAIOrchestrator(manager).analyze(clean_question, user_id=user_id)
        await persist_decision(result, user_id)
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

    return asyncio.run(run_pipeline())
