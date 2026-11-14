import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from ayuai.database.connection import Base
from ayuai.database.repositories_users import UserRepository

@pytest.mark.asyncio
async def test_user_registration_and_login():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        repo = UserRepository(session)
        user = await repo.create("Ayu", "long-enough-password")
        await session.commit()
        assert (await repo.authenticate("ayu", "long-enough-password")).id == user.id
        assert await repo.authenticate("ayu", "wrong-password") is None
        with pytest.raises(ValueError):
            await repo.create("ayu", "another-long-password")
    await engine.dispose()
