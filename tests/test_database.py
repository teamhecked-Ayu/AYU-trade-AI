import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from ayuai.database.connection import Base
from ayuai.database.models import DecisionModel

@pytest.mark.asyncio
async def test_decision_persists_in_database():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        session.add(DecisionModel(id="d1", user_id="u1", question="BTC?", action="WAIT", confidence=.7))
        await session.commit()
        result = await session.execute(select(DecisionModel))
        assert result.scalar_one().action == "WAIT"
    await engine.dispose()


import uuid
from datetime import datetime, timedelta, timezone

from ayuai.database.repositories import DecisionRepository


@pytest.mark.asyncio
async def test_decision_history_is_recent_and_user_scoped():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(timezone.utc)
    async with Session() as session:
        session.add_all([
            DecisionModel(
                id="a",
                user_id="user-1",
                question="Old result",
                action="WAIT",
                confidence=0.3,
                created_at=now - timedelta(days=2),
            ),
            DecisionModel(
                id="b",
                user_id="user-1",
                question="Newest result",
                action="HOLD",
                confidence=0.8,
                created_at=now,
            ),
            DecisionModel(
                id="c",
                user_id="user-2",
                question="Another user's result",
                action="SELL",
                confidence=0.9,
                created_at=now + timedelta(seconds=1),
            ),
        ])
        await session.commit()

        rows = await DecisionRepository(session).list_recent("user-1", limit=1)
        assert len(rows) == 1
        assert rows[0].id == "b"
        assert rows[0].question == "Newest result"
    await engine.dispose()
