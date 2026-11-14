import pytest

from ayuai.jobs.analysis import AnalysisJob
from ayuai.jobs import events


@pytest.mark.asyncio
async def test_event_stream_emits_only_changed_state(monkeypatch):
    jobs = [
        AnalysisJob("abc", "PENDING"),
        AnalysisJob("abc", "PENDING"),
        AnalysisJob("abc", "SUCCESS", {"status": "completed"}),
    ]

    monkeypatch.setattr(events, "get_analysis_job", lambda _: jobs.pop(0))

    received = []
    async for item in events.analysis_events("abc", interval_seconds=0):
        received.append(item)

    assert len(received) == 2
    assert '"state":"PENDING"' in received[0]
    assert '"state":"SUCCESS"' in received[1]
