"""Celery task entry points.

Heavy analysis belongs here rather than inside synchronous API handlers.
"""
from __future__ import annotations
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
