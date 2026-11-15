from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
import pytest

from ayuai.database.connection import Base
from ayuai.database.models import AnalysisJobModel
from ayuai.jobs.analysis import submit_analysis


@pytest.mark.asyncio
async def test_submit_analysis_registers_job_owner(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    def fake_send_task(name, *, kwargs, task_id):
        assert name == "ayuai.analyze_question"
        assert kwargs == {"question": "Analyze a sample", "user_id": "user-1"}
        return type("FakeTask", (), {"id": task_id, "state": "PENDING"})()

    monkeypatch.setattr("ayuai.jobs.analysis.celery_app.send_task", fake_send_task)

    async with sessions() as session:
        job = await submit_analysis("Analyze a sample", "user-1", session)
        assert job.state == "PENDING"

    async with sessions() as session:
        record = (
            await session.execute(
                select(AnalysisJobModel).where(AnalysisJobModel.job_id == job.job_id)
            )
        ).scalar_one()
        assert record.user_id == "user-1"

    await engine.dispose()
