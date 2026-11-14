"""Server-sent analysis job updates without exposing task internals."""
from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from .analysis import get_analysis_job

TERMINAL_STATES = {"SUCCESS", "FAILURE", "REVOKED"}


async def analysis_events(job_id: str, *, interval_seconds: float = 1.0) -> AsyncIterator[str]:
    """Yield normalized job status events until the job reaches a terminal state."""
    last_payload: str | None = None
    while True:
        job = get_analysis_job(job_id)
        payload = {
            "job_id": job.job_id,
            "state": job.state,
            "result": job.result,
        }
        encoded = json.dumps(payload, default=str, separators=(",", ":"))
        if encoded != last_payload:
            yield f"event: analysis\ndata: {encoded}\n\n"
            last_payload = encoded
        if job.state.upper() in TERMINAL_STATES:
            return
        await asyncio.sleep(interval_seconds)
