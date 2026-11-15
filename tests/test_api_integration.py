"""API integration tests for the public analysis flow.

External systems are replaced with deterministic fakes so these tests verify
the API contract without requiring Redis, Celery workers, or AI providers.
"""

from fastapi.testclient import TestClient

from api.main import app, current_user, get_session
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
    async def fake_submit(question, user_id, session):
        return AnalysisJob("job-123", "PENDING")

    async def allow_job_owner(job_id, user_id, session):
        return None

    app.dependency_overrides[current_user] = lambda: "user-1"
    try:
        monkeypatch.setattr("api.main.submit_analysis", fake_submit)
        monkeypatch.setattr("api.main.require_analysis_job_owner", allow_job_owner)
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

    async def allow_job_owner(job_id, user_id, session):
        return None

    app.dependency_overrides[current_user] = lambda: "user-1"
    try:
        monkeypatch.setattr("api.main.require_analysis_job_owner", allow_job_owner)
        monkeypatch.setattr("api.main.analysis_events", fake_events)
        client = TestClient(app)
        response = client.get("/analysis/job-123/events")
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        assert '"state":"PENDING"' in response.text
        assert '"state":"SUCCESS"' in response.text
    finally:
        app.dependency_overrides.clear()


def test_cors_preflight_allows_local_dashboard():
    client = TestClient(app)
    response = client.options(
        "/analysis",
        headers={
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:8080"
    assert "authorization" in response.headers["access-control-allow-headers"].lower()


def test_cors_preflight_rejects_unknown_origin():
    client = TestClient(app)
    response = client.options(
        "/analysis",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_decision_history_is_scoped_to_authenticated_user(monkeypatch):
    from datetime import datetime, timezone
    from types import SimpleNamespace

    app.dependency_overrides[current_user] = lambda: "user-1"

    class FakeRepository:
        def __init__(self, session):
            assert session is not None

        async def list_recent(self, user_id, *, limit=25):
            assert user_id == "user-1"
            assert limit == 10
            return [
                SimpleNamespace(
                    id="decision-1",
                    question="Explain a sample market scenario",
                    action="WAIT",
                    confidence=0.4,
                    outcome=None,
                    created_at=datetime(2026, 11, 15, tzinfo=timezone.utc),
                )
            ]

    try:
        monkeypatch.setattr("api.main.DecisionRepository", FakeRepository)
        async def fake_session():
            yield object()
        app.dependency_overrides[get_session] = fake_session

        response = TestClient(app).get("/decisions?limit=10")
        assert response.status_code == 200
        body = response.json()
        assert len(body["decisions"]) == 1
        assert body["decisions"][0]["id"] == "decision-1"
        assert body["decisions"][0]["action"] == "WAIT"
    finally:
        app.dependency_overrides.clear()
