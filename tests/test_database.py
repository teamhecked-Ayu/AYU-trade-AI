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
