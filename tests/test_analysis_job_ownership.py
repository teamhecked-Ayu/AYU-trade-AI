import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from api.main import require_analysis_job_owner
from ayuai.database.connection import Base
from ayuai.database.models import AnalysisJobModel


@pytest.mark.asyncio
async def test_analysis_job_access_is_limited_to_its_owner():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async with sessions() as session:
        session.add(AnalysisJobModel(job_id="job-123", user_id="owner-1"))
        await session.commit()

        await require_analysis_job_owner("job-123", "owner-1", session)

        with pytest.raises(HTTPException) as error:
            await require_analysis_job_owner("job-123", "other-user", session)
        assert error.value.status_code == 404

        with pytest.raises(HTTPException) as missing:
            await require_analysis_job_owner("missing-job", "owner-1", session)
        assert missing.value.status_code == 404

    await engine.dispose()
