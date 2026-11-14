"""Persistent user account repository."""
from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import UserModel
from ayuai.security.auth import hash_password, verify_password

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, username: str, password: str) -> UserModel:
        username = username.strip().lower()
        if not username or len(username) > 64:
            raise ValueError("Invalid username.")
        existing = (await self.session.execute(select(UserModel).where(UserModel.username == username))).scalar_one_or_none()
        if existing:
            raise ValueError("Username already exists.")
        user = UserModel(id=str(uuid.uuid4()), username=username, password_hash=hash_password(password))
        self.session.add(user)
        await self.session.flush()
        return user

    async def authenticate(self, username: str, password: str) -> UserModel | None:
        username = username.strip().lower()
        user = (await self.session.execute(select(UserModel).where(UserModel.username == username))).scalar_one_or_none()
        if user is None or not verify_password(password, user.password_hash):
            return None
        return user
