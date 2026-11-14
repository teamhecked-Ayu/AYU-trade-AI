"""AYUAI authenticated API boundary with database-backed user accounts."""
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from ayuai.database.connection import SessionLocal
from ayuai.database.repositories_users import UserRepository
from ayuai.security.auth import AuthenticationError, issue_token, verify_token

app = FastAPI(title="AYUAI API", version="0.2.0")

class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=10, max_length=256)

async def get_session():
    async with SessionLocal() as session:
        yield session

async def current_user(authorization: str | None = Header(default=None)) -> str:
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
async def register(request: Credentials, session: AsyncSession = Depends(get_session)):
    try:
        user = await UserRepository(session).create(request.username, request.password)
        await session.commit()
    except ValueError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail=str(exc))
    return {"user_id": user.id, "username": user.username}

@app.post("/auth/login")
async def login(request: Credentials, session: AsyncSession = Depends(get_session)):
    user = await UserRepository(session).authenticate(request.username, request.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": issue_token(user.id), "token_type": "bearer"}

@app.get("/auth/me")
async def me(user_id: str = Depends(current_user)):
    return {"user_id": user_id}
