"""AYUAI authenticated API boundary with database-backed user accounts."""

import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ayuai.database.connection import SessionLocal, engine as database_engine
from ayuai.database.repositories_users import UserRepository
from ayuai.database.repositories import DecisionRepository
from ayuai.jobs.analysis import (
    analysis_job_belongs_to_user,
    get_analysis_job,
    submit_analysis,
)
from ayuai.jobs.events import analysis_events
from ayuai.database.repositories_credentials import ProviderCredentialRepository
from ayuai.security.auth import AuthenticationError, issue_token, verify_token
from ayuai.security.audit import AuditEvent
from ayuai.security.key_vault import KeyVault, CredentialError
from ayuai.security.rate_limit import RateLimit, RateLimiter
from ayuai.security.redis_rate_limit import RedisRateLimiter, RateLimitBackendUnavailable

@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        yield
    finally:
        await redis_auth_limiter.close()
        await redis_api_limiter.close()


app = FastAPI(title="AYUAI API", version="0.4.0", lifespan=lifespan)

# The static dashboard runs on a separate origin during local development.
# Production deployments should add their exact frontend origins in .env.
cors_origins = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "AYUAI_CORS_ORIGINS",
        "http://localhost:8080,http://127.0.0.1:8080",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    max_age=600,
)

# Authentication endpoints get a stricter bucket. Normal authenticated API
# calls get a separate allowance so dashboard polling does not block itself.
AUTH_RATE_LIMIT = RateLimit(requests=10, window_seconds=60)
API_RATE_LIMIT = RateLimit(requests=120, window_seconds=60)
RATE_LIMIT_BACKEND = os.getenv("AYUAI_RATE_LIMIT_BACKEND", "memory").strip().lower()
if RATE_LIMIT_BACKEND not in {"memory", "redis"}:
    raise RuntimeError("AYUAI_RATE_LIMIT_BACKEND must be 'memory' or 'redis'.")

auth_limiter = RateLimiter(AUTH_RATE_LIMIT)
api_limiter = RateLimiter(API_RATE_LIMIT)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_auth_limiter = RedisRateLimiter(redis_url, AUTH_RATE_LIMIT)
redis_api_limiter = RedisRateLimiter(redis_url, API_RATE_LIMIT)


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=10, max_length=256)


class ProviderKeyRequest(BaseModel):
    provider: str = Field(min_length=2, max_length=32)
    api_key: str = Field(min_length=8, max_length=512)


class AnalysisRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10000)


async def get_session():
    async with SessionLocal() as session:
        yield session


def client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


async def enforce_rate_limit(request: Request, *, scope: str = "api") -> None:
    """Apply separate shared counters for authentication and normal API traffic."""
    if scope not in {"auth", "api"}:
        raise ValueError("Unknown rate-limit scope.")

    ip_address = client_key(request)
    limiter_key = f"{scope}:{ip_address}"
    memory_limiter = auth_limiter if scope == "auth" else api_limiter
    redis_limiter = redis_auth_limiter if scope == "auth" else redis_api_limiter

    try:
        if RATE_LIMIT_BACKEND == "redis":
            allowed, retry_after = await redis_limiter.check(limiter_key)
        else:
            allowed, retry_after = memory_limiter.check(limiter_key)
    except RateLimitBackendUnavailable as exc:
        AuditEvent("rate_limit_backend_unavailable", ip=ip_address, status="blocked").write()
        raise HTTPException(
            status_code=503,
            detail="Rate limit service is temporarily unavailable.",
        ) from exc

    if not allowed:
        AuditEvent("rate_limited", ip=ip_address, status="blocked").write()
        raise HTTPException(
            status_code=429,
            detail="Too many requests",
            headers={"Retry-After": str(retry_after)},
        )


async def current_user(
    request: Request,
    authorization: str | None = Header(default=None),
) -> str:
    await enforce_rate_limit(request, scope="api")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        return verify_token(authorization[7:])
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def require_analysis_job_owner(
    job_id: str,
    user_id: str,
    session: AsyncSession,
) -> None:
    """Hide missing and foreign jobs behind the same not-found response."""
    if not await analysis_job_belongs_to_user(session, job_id, user_id):
        raise HTTPException(status_code=404, detail="Analysis job not found")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def readiness():
    """Report readiness only when required secrets and runtime services work."""
    required_secrets = (
        "AYU_API_KEY",
        "AYUAI_AUTH_SECRET",
        "AYUAI_KEY_VAULT_SECRET",
        "POSTGRES_PASSWORD",
    )
    missing = [name for name in required_secrets if not os.getenv(name)]
    if missing:
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "missing_configuration": missing},
        )

    try:
        async with database_engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

        if RATE_LIMIT_BACKEND == "redis":
            await redis_auth_limiter.client.ping()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="A required database or rate-limit service is unavailable.",
        ) from exc

    return {
        "status": "ready",
        "dependencies": {
            "database": "ok",
            "rate_limiter": RATE_LIMIT_BACKEND,
        },
        "paper_mode": os.getenv("PAPER_TRADE", "true").lower() == "true",
    }


@app.post("/auth/register", status_code=201)
async def register(
    request: Request,
    credentials: Credentials,
    session: AsyncSession = Depends(get_session),
):
    await enforce_rate_limit(request, scope="auth")
    try:
        user = await UserRepository(session).create(credentials.username, credentials.password)
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail=str(exc))
    return {"user_id": user.id, "username": user.username}


@app.post("/auth/login")
async def login(
    request: Request,
    credentials: Credentials,
    session: AsyncSession = Depends(get_session),
):
    await enforce_rate_limit(request, scope="auth")
    user = await UserRepository(session).authenticate(credentials.username, credentials.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": issue_token(user.id), "token_type": "bearer"}


@app.get("/auth/me")
async def me(user_id: str = Depends(current_user)):
    return {"user_id": user_id}


@app.post("/analysis", status_code=202)
async def create_analysis(
    payload: AnalysisRequest,
    user_id: str = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        job = await submit_analysis(payload.question, user_id, session)
    except Exception as exc:
        await session.rollback()
        raise HTTPException(status_code=503, detail="Analysis queue is unavailable.") from exc
    AuditEvent("analysis_submitted", user_id=user_id, status="queued").write()
    return {"job_id": job.job_id, "state": job.state}


@app.get("/analysis/{job_id}/events")
async def analysis_event_stream(
    job_id: str,
    user_id: str = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    await require_analysis_job_owner(job_id, user_id, session)
    return StreamingResponse(
        analysis_events(job_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/analysis/{job_id}")
async def analysis_status(
    job_id: str,
    user_id: str = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    await require_analysis_job_owner(job_id, user_id, session)
    job = get_analysis_job(job_id)
    return {"job_id": job.job_id, "state": job.state, "result": job.result}


@app.get("/decisions")
async def decision_history(
    limit: int = Query(default=25, ge=1, le=100),
    user_id: str = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return only the authenticated user's latest saved analysis decisions."""
    rows = await DecisionRepository(session).list_recent(user_id, limit=limit)
    return {
        "decisions": [
            {
                "id": row.id,
                "question": row.question,
                "action": row.action,
                "confidence": row.confidence,
                "outcome": row.outcome,
                "created_at": row.created_at,
            }
            for row in rows
        ]
    }


@app.get("/providers")
async def list_provider_keys(
    user_id: str = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    providers = await ProviderCredentialRepository(session, KeyVault()).list_providers(user_id)
    return {"providers": providers}


@app.put("/providers/{provider}")
async def store_provider_key(
    provider: str,
    payload: ProviderKeyRequest,
    user_id: str = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    if provider.lower() != payload.provider.lower():
        raise HTTPException(status_code=400, detail="Provider path and payload must match.")
    try:
        await ProviderCredentialRepository(session, KeyVault()).store(
            user_id, provider, payload.api_key
        )
        await session.commit()
    except (ValueError, CredentialError) as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    AuditEvent("provider_key_updated", user_id=user_id, status=provider.lower()).write()
    return {"provider": provider.lower(), "stored": True}


@app.delete("/providers/{provider}")
async def delete_provider_key(
    provider: str,
    user_id: str = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    deleted = await ProviderCredentialRepository(session, KeyVault()).delete(user_id, provider)
    if deleted:
        await session.commit()
    return {"provider": provider.lower(), "deleted": deleted}
