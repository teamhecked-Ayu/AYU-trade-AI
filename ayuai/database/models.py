from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from .connection import Base

class DecisionModel(Base):
    __tablename__ = "decisions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    question: Mapped[str] = mapped_column(Text)
    action: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[float] = mapped_column(Float)
    outcome: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class AgentPerformanceModel(Base):
    __tablename__ = "agent_performance"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    agent: Mapped[str] = mapped_column(String(128), index=True)
    predictions: Mapped[int] = mapped_column(default=0)
    correct: Mapped[int] = mapped_column(default=0)
