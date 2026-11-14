import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from ayuai.database.connection import Base
from ayuai.database.repositories import DecisionRepository, AgentPerformanceRepository
from ayuai.database.analytics import decision_analytics

@pytest.mark.asyncio
async def test_persistent_memory_and_analytics_are_user_isolated():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        decisions = DecisionRepository(session)
        agents = AgentPerformanceRepository(session)
        await decisions.create(id="d1", user_id="u1", question="BTC?", action="BUY", confidence=.8)
        await decisions.record_outcome("d1", "u1", .05)
        await agents.record("u1", "agent-a", True)
        analytics = await decision_analytics(session, "u1")
        assert analytics["resolved"] == 1
        assert analytics["win_rate"] == 1.0
        assert (await agents.accuracy("u1"))["agent-a"] == 1.0
    await engine.dispose()
