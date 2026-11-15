"""AYUAI authenticated API boundary with database-backed user accounts."""

import os

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ayuai.database.connection import SessionLocal
from ayuai.database.repositories_users import UserRepository
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

app = FastAPI(title="AYUAI API", version="0.4.0")

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

AUTH_RATE_LIMIT = RateLimit(requests=10, window_seconds=60)
RATE_LIMIT_BACKEND = os.getenv("AYUAI_RATE_LIMIT_BACKEND", "memory").strip().lower()
if RATE_LIMIT_BACKEND not in {"memory", "redis"}:
    raise RuntimeError("AYUAI_RATE_LIMIT_BACKEND must be 'memory' or 'redis'.")

auth_limiter = RateLimiter(AUTH_RATE_LIMIT)
redis_auth_limiter = RedisRateLimiter(
    os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    AUTH_RATE_LIMIT,
)
app.add_event_handler("shutdown", redis_auth_limiter.close)


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


async def enforce_rate_limit(request: Request) -> None:
    ip_address = client_key(request)
    try:
        if RATE_LIMIT_BACKEND == "redis":
            allowed, retry_after = await redis_auth_limiter.check(ip_address)
        else:
            allowed, retry_after = auth_limiter.check(ip_address)
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
    await enforce_rate_limit(request)
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


@app.post("/auth/register", status_code=201)
async def register(
    request: Request,
    credentials: Credentials,
    session: AsyncSession = Depends(get_session),
):
    await enforce_rate_limit(request)
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
    enforce_rate_limit(request)
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
