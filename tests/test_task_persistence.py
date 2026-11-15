from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ayuai.database.connection import Base
from ayuai.database.models import DecisionModel
from ayuai.jobs.tasks import persist_decision


@pytest.mark.asyncio
async def test_celery_analysis_decision_is_persisted_for_its_user(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    sessions = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def test_session_scope():
        async with sessions() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    monkeypatch.setattr("ayuai.database.connection.session_scope", test_session_scope)

    result = SimpleNamespace(
        question="Evaluate a sample market scenario",
        decision=SimpleNamespace(conclusion="WAIT", confidence=0.65),
        decision_id=None,
    )

    decision_id = await persist_decision(result, "user-123")

    assert decision_id
    assert result.decision_id == decision_id
    async with sessions() as session:
        stored = (
            await session.execute(
                select(DecisionModel).where(DecisionModel.id == decision_id)
            )
        ).scalar_one()
        assert stored.user_id == "user-123"
        assert stored.question == "Evaluate a sample market scenario"
        assert stored.action == "WAIT"
        assert stored.confidence == 0.65

    await engine.dispose()
