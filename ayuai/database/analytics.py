"""Performance analytics built from persisted, resolved decisions."""
from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import DecisionModel

async def decision_analytics(session: AsyncSession, user_id: str) -> dict:
    rows = (await session.execute(select(DecisionModel).where(
        DecisionModel.user_id == user_id,
        DecisionModel.outcome.is_not(None),
    ))).scalars().all()
    if not rows:
        return {"resolved": 0, "win_rate": None, "average_outcome": None, "confidence_calibration": None}

    wins = sum(1 for row in rows if row.outcome > 0)
    avg_outcome = sum(float(row.outcome) for row in rows) / len(rows)
    avg_confidence = sum(float(row.confidence) for row in rows) / len(rows)
    return {
        "resolved": len(rows),
        "win_rate": wins / len(rows),
        "average_outcome": avg_outcome,
        "confidence_calibration": avg_confidence,
    }
