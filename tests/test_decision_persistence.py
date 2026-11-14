import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from ayuai.database.connection import Base
from ayuai.database.repositories import DecisionRepository

@pytest.mark.asyncio
async def test_outcome_cannot_cross_user_boundary():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        repo = DecisionRepository(session)
        await repo.create(id="d1", user_id="owner", question="BTC?", action="WAIT", confidence=.5)
        with pytest.raises(KeyError):
            await repo.record_outcome("d1", "other-user", .1)
    await engine.dispose()
