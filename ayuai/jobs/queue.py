"""Background task queue abstraction for AYUAI.

The default backend is intentionally simple for local development. Redis is used
as the shared broker/result backend when Celery workers are enabled.
"""
from __future__ import annotations
from dataclasses import dataclass
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


@dataclass(frozen=True)
class TaskStatus:
    task_id: str
    state: str


def celery_available() -> bool:
    try:
        import celery  # noqa: F401
        return True
    except ImportError:
        return False
