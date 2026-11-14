"""API integration tests for the public analysis flow.

External systems are replaced with deterministic fakes so these tests verify
the API contract without requiring Redis, Celery workers, or AI providers.
"""
from fastapi.testclient import TestClient

from api.main import app, current_user
from ayuai.jobs.analysis import AnalysisJob


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analysis_requires_authentication():
    client = TestClient(app)
    response = client.post("/analysis", json={"question": "Should I buy BTC?"})
    assert response.status_code == 401


def test_analysis_submit_and_status_flow(monkeypatch):
    app.dependency_overrides[current_user] = lambda: "user-1"
    try:
        monkeypatch.setattr(
            "api.main.submit_analysis",
            lambda question, user_id: AnalysisJob("job-123", "PENDING"),
        )
        monkeypatch.setattr(
            "api.main.get_analysis_job",
            lambda job_id: AnalysisJob(
                job_id, "SUCCESS", {"conclusion": "test result", "confidence": 0.8}
            ),
        )

        client = TestClient(app)
        created = client.post("/analysis", json={"question": "Should I buy BTC?"})
        assert created.status_code == 202
        assert created.json() == {"job_id": "job-123", "state": "PENDING"}

        status = client.get("/analysis/job-123")
        assert status.status_code == 200
        body = status.json()
        assert body["state"] == "SUCCESS"
        assert body["result"]["conclusion"] == "test result"
    finally:
        app.dependency_overrides.clear()


def test_analysis_event_stream_contract(monkeypatch):
    async def fake_events(job_id):
        yield 'data: {"job_id":"job-123","state":"PENDING"}\n\n'
        yield 'data: {"job_id":"job-123","state":"SUCCESS"}\n\n'

    app.dependency_overrides[current_user] = lambda: "user-1"
    try:
        monkeypatch.setattr("api.main.analysis_events", fake_events)
        client = TestClient(app)
        response = client.get("/analysis/job-123/events")
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        assert '"state":"PENDING"' in response.text
        assert '"state":"SUCCESS"' in response.text
    finally:
        app.dependency_overrides.clear()
