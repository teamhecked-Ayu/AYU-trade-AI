"""AYUAI authenticated API boundary with database-backed user accounts."""
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from ayuai.database.connection import SessionLocal
from ayuai.database.repositories_users import UserRepository
from ayuai.security.auth import AuthenticationError, issue_token, verify_token
from ayuai.security.audit import AuditEvent
from ayuai.security.rate_limit import RateLimit, RateLimiter
from ayuai.jobs.analysis import get_analysis_job, submit_analysis
from ayuai.database.repositories_credentials import ProviderCredentialRepository
from ayuai.security.key_vault import KeyVault, CredentialError

app = FastAPI(title="AYUAI API", version="0.4.0")
auth_limiter = RateLimiter(RateLimit(requests=10, window_seconds=60))

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


def enforce_rate_limit(request: Request) -> None:
    allowed, retry_after = auth_limiter.check(client_key(request))
    if not allowed:
        AuditEvent("rate_limited", ip=client_key(request), status="blocked").write()
        raise HTTPException(status_code=429, detail="Too many requests",
                            headers={"Retry-After": str(retry_after)})


async def current_user(request: Request, authorization: str | None = Header(default=None)) -> str:
    enforce_rate_limit(request)
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        return verify_token(authorization[7:])
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/auth/register", status_code=201)
async def register(request: Request, credentials: Credentials, session: AsyncSession = Depends(get_session)):
    enforce_rate_limit(request)
    try:
        user = await UserRepository(session).create(credentials.username, credentials.password)
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail=str(exc))
    return {"user_id": user.id, "username": user.username}

@app.post("/auth/login")
async def login(request: Request, credentials: Credentials, session: AsyncSession = Depends(get_session)):
    enforce_rate_limit(request)
    user = await UserRepository(session).authenticate(credentials.username, credentials.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": issue_token(user.id), "token_type": "bearer"}

@app.get("/auth/me")
async def me(user_id: str = Depends(current_user)):
    return {"user_id": user_id}


@app.post("/analysis", status_code=202)
async def create_analysis(payload: AnalysisRequest, user_id: str = Depends(current_user)):
    job = submit_analysis(payload.question, user_id)
    AuditEvent("analysis_submitted", user_id=user_id, status="queued").write()
    return {"job_id": job.job_id, "state": job.state}


@app.get("/analysis/{job_id}")
async def analysis_status(job_id: str, user_id: str = Depends(current_user)):
    job = get_analysis_job(job_id)
    return {"job_id": job.job_id, "state": job.state, "result": job.result}


@app.get("/providers")
async def list_provider_keys(user_id: str = Depends(current_user), session: AsyncSession = Depends(get_session)):
    providers = await ProviderCredentialRepository(session, KeyVault()).list_providers(user_id)
    return {"providers": providers}


@app.put("/providers/{provider}")
async def store_provider_key(provider: str, payload: ProviderKeyRequest, user_id: str = Depends(current_user), session: AsyncSession = Depends(get_session)):
    if provider.lower() != payload.provider.lower():
        raise HTTPException(status_code=400, detail="Provider path and payload must match.")
    try:
        await ProviderCredentialRepository(session, KeyVault()).store(user_id, provider, payload.api_key)
        await session.commit()
    except (ValueError, CredentialError) as exc:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    AuditEvent("provider_key_updated", user_id=user_id, status=provider.lower()).write()
    return {"provider": provider.lower(), "stored": True}


@app.delete("/providers/{provider}")
async def delete_provider_key(provider: str, user_id: str = Depends(current_user), session: AsyncSession = Depends(get_session)):
    deleted = await ProviderCredentialRepository(session, KeyVault()).delete(user_id, provider)
    if deleted:
        await session.commit()
    return {"provider": provider.lower(), "deleted": deleted}
