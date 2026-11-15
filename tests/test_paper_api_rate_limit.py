from fastapi.testclient import TestClient

from api import app
from api import main as api_main


def test_paper_endpoints_use_shared_paper_rate_limit(monkeypatch):
    calls = []

    async def fake_enforce(request, *, scope="api"):
        calls.append(scope)

    monkeypatch.setenv("AYU_API_KEY", "test-paper-key")
    monkeypatch.setattr(api_main, "enforce_rate_limit", fake_enforce)

    client = TestClient(app)
    headers = {"X-API-Key": "test-paper-key"}

    metrics = client.get("/metrics", headers=headers)
    portfolio = client.get("/portfolio", headers=headers)

    assert metrics.status_code == 200
    assert portfolio.status_code == 200
    assert calls == ["paper", "paper"]


def test_paper_endpoints_apply_rate_limit_before_api_key_validation(monkeypatch):
    calls = []

    async def fake_enforce(request, *, scope="api"):
        calls.append(scope)

    monkeypatch.setattr(api_main, "enforce_rate_limit", fake_enforce)
    client = TestClient(app)

    response = client.get("/portfolio", headers={"X-API-Key": "wrong"})

    assert response.status_code == 401
    assert calls == ["paper"]
