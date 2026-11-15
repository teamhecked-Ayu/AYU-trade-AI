"""End-to-end smoke test executed inside the Docker Compose API container."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
import uuid

BASE_URL = "http://127.0.0.1:8000"


def request_json(path: str, *, method: str = "GET", payload=None, headers=None):
    request_headers = {"Accept": "application/json"}
    if payload is not None:
        request_headers["Content-Type"] = "application/json"
    if headers:
        request_headers.update(headers)
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        BASE_URL + path,
        data=body,
        headers=request_headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} returned {exc.code}: {detail}") from exc


def wait_for_readiness() -> dict:
    last_error: Exception | None = None
    for _ in range(90):
        try:
            status, body = request_json("/ready")
            if status == 200 and body.get("status") == "ready":
                return body
            last_error = RuntimeError(f"Unexpected readiness response: {body}")
        except Exception as exc:
            last_error = exc
        time.sleep(2)
    raise RuntimeError(f"API did not become ready: {last_error}")


def verify_migrations() -> None:
    from sqlalchemy import create_engine, inspect

    url = os.environ["DATABASE_URL"].replace("+asyncpg", "+psycopg")
    engine = create_engine(url, pool_pre_ping=True)
    try:
        tables = set(inspect(engine).get_table_names())
        required = {
            "users",
            "decisions",
            "agent_performance",
            "provider_credentials",
            "analysis_jobs",
        }
        missing = sorted(required - tables)
        if missing:
            raise RuntimeError(f"Database migrations missing tables: {missing}")
    finally:
        engine.dispose()


def main() -> None:
    readiness = wait_for_readiness()
    if readiness.get("paper_mode") is not True:
        raise RuntimeError("Compose did not start in paper mode.")
    verify_migrations()

    username = "smoke_" + uuid.uuid4().hex[:12]
    password = "smoke-test-password-2026"

    status, created = request_json(
        "/auth/register",
        method="POST",
        payload={"username": username, "password": password},
    )
    if status != 201 or not created.get("user_id"):
        raise RuntimeError(f"Account registration failed: {created}")

    _, login = request_json(
        "/auth/login",
        method="POST",
        payload={"username": username, "password": password},
    )
    token = login.get("access_token")
    if not token:
        raise RuntimeError("Login did not return an access token.")
    bearer = {"Authorization": "Bearer " + token}

    request_json(
        "/providers/openai",
        method="PUT",
        headers=bearer,
        payload={"provider": "openai", "api_key": "ci-provider-key-not-real-12345"},
    )
    _, providers = request_json("/providers", headers=bearer)
    if "openai" not in [str(item).lower() for item in providers.get("providers", [])]:
        raise RuntimeError(f"Provider key was not stored: {providers}")

    _, history = request_json("/decisions?limit=5", headers=bearer)
    if history.get("decisions") != []:
        raise RuntimeError(f"New account should have empty history: {history}")

    # This verifies that Redis accepted the message and a separate Celery
    # worker actually consumed it and wrote the result backend response.
    from ayuai.jobs.tasks import health_check

    worker_result = health_check.delay().get(timeout=30)
    if worker_result != {"status": "ok"}:
        raise RuntimeError(f"Celery worker did not return a healthy result: {worker_result}")

    api_key = os.environ["AYU_API_KEY"]
    request_json(
        "/paper/orders",
        method="POST",
        headers={"X-API-Key": api_key},
        payload={
            "symbol": "SMOKE/USDT",
            "side": "buy",
            "quantity": 1,
            "price": 25,
        },
    )
    _, portfolio = request_json(
        "/portfolio",
        headers={"X-API-Key": api_key},
    )
    position = portfolio.get("positions", {}).get("SMOKE/USDT")
    if not position or float(position.get("quantity", 0)) != 1:
        raise RuntimeError(f"Paper order was not reflected in the portfolio: {portfolio}")

    print(
        "Compose smoke test passed: readiness, PostgreSQL migrations, "
        "registration/login, encrypted provider storage, decision history, "
        "Redis/Celery worker, and persistent paper order."
    )


if __name__ == "__main__":
    main()
