"""Asynchronous AYUAI analysis job registry.

Celery executes the heavy work. The registry stores only serializable task
metadata in Redis; sensitive provider keys remain server-side.
"""
from __future__ import annotations
from dataclasses import dataclass
from celery.result import AsyncResult
from ayuai.jobs.tasks import celery_app


@dataclass(frozen=True)
class AnalysisJob:
    job_id: str
    state: str
    result: dict | None = None


def submit_analysis(question: str, user_id: str) -> AnalysisJob:
    task = celery_app.send_task(
        "ayuai.analyze_question",
        kwargs={"question": question, "user_id": user_id},
    )
    return AnalysisJob(job_id=task.id, state=task.state)


def get_analysis_job(job_id: str) -> AnalysisJob:
    task = AsyncResult(job_id, app=celery_app)
    result = task.result if task.successful() and isinstance(task.result, dict) else None
    return AnalysisJob(job_id=job_id, state=task.state, result=result)
