"""Persistent repositories for AYUAI decisions and agent performance."""
from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import AgentPerformanceModel, DecisionModel

class DecisionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, *, id: str, user_id: str, question: str, action: str, confidence: float) -> DecisionModel:
        row = DecisionModel(id=id, user_id=user_id, question=question, action=action, confidence=confidence)
        self.session.add(row)
        await self.session.flush()
        return row

    async def record_outcome(self, decision_id: str, user_id: str, outcome: float) -> DecisionModel:
        row = await self.session.get(DecisionModel, decision_id)
        if row is None or row.user_id != user_id:
            raise KeyError("Unknown decision")
        row.outcome = float(outcome)
        await self.session.flush()
        return row

    async def summary(self, user_id: str) -> dict:
        rows = (await self.session.execute(select(DecisionModel).where(DecisionModel.user_id == user_id))).scalars().all()
        resolved = [r for r in rows if r.outcome is not None]
        return {"total_decisions": len(rows), "resolved_decisions": len(resolved)}

class AgentPerformanceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record(self, user_id: str, agent: str, correct: bool) -> AgentPerformanceModel:
        stmt = select(AgentPerformanceModel).where(
            AgentPerformanceModel.user_id == user_id,
            AgentPerformanceModel.agent == agent,
        )
        row = (await self.session.execute(stmt)).scalar_one_or_none()
        if row is None:
            row = AgentPerformanceModel(user_id=user_id, agent=agent)
            self.session.add(row)
        row.predictions += 1
        row.correct += int(correct)
        await self.session.flush()
        return row

    async def accuracy(self, user_id: str) -> dict[str, float | None]:
        rows = (await self.session.execute(select(AgentPerformanceModel).where(AgentPerformanceModel.user_id == user_id))).scalars().all()
        return {r.agent: (r.correct / r.predictions if r.predictions else None) for r in rows}
