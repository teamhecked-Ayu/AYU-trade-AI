"""Outcome evaluation service for persistent AYUAI decisions."""
from sqlalchemy.ext.asyncio import AsyncSession
from .repositories import DecisionRepository

async def record_decision_outcome(session: AsyncSession, *, decision_id: str, user_id: str, outcome: float):
    row = await DecisionRepository(session).record_outcome(decision_id, user_id, outcome)
    await session.commit()
    return row
