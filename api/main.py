"""Minimal authenticated API boundary for AYUAI."""
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from ayuai.security.auth import AuthenticationError, issue_token, verify_token

app = FastAPI(title="AYUAI API", version="0.1.0")

class TokenRequest(BaseModel):
    user_id: str

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/auth/token")
async def token(request: TokenRequest):
    # Identity verification must be connected before public deployment.
    return {"access_token": issue_token(request.user_id), "token_type": "bearer"}

@app.get("/auth/me")
async def me(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        return {"user_id": verify_token(authorization[7:])}
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
