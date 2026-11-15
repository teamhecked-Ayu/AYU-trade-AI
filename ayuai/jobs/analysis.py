"""Analysis job submission and ownership-aware lookup helpers."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from celery.result import AsyncResult
from sqlalchemy.ext.asyncio import AsyncSession

from ayuai.database.models import AnalysisJobModel
from ayuai.jobs.tasks import celery_app


@dataclass(frozen=True)
class AnalysisJob:
    job_id: str
    state: str
    result: dict | None = None


async def submit_analysis(
    question: str,
    user_id: str,
    session: AsyncSession,
) -> AnalysisJob:
    """Register the owner before queueing work, then use the same ID in Celery."""
    job_id = str(uuid4())
    record = AnalysisJobModel(job_id=job_id, user_id=user_id)
    session.add(record)
    await session.commit()

    try:
        task = celery_app.send_task(
            "ayuai.analyze_question",
            kwargs={"question": question, "user_id": user_id},
            task_id=job_id,
        )
    except Exception:
        await session.delete(record)
        await session.commit()
        raise

    return AnalysisJob(job_id=job_id, state=task.state)


async def analysis_job_belongs_to_user(
    session: AsyncSession,
    job_id: str,
    user_id: str,
) -> bool:
    """Return whether a submitted job is owned by the authenticated user."""
    record = await session.get(AnalysisJobModel, job_id)
    return record is not None and record.user_id == user_id


def get_analysis_job(job_id: str) -> AnalysisJob:
    task = AsyncResult(job_id, app=celery_app)
    result = task.result if task.successful() and isinstance(task.result, dict) else None
    return AnalysisJob(job_id=job_id, state=task.state, result=result)
