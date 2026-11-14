"""Decision and agent performance memory.

Memory records outcomes; it does not silently retrain models or change trading
rules without explicit evaluation.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any
import uuid

@dataclass
class DecisionRecord:
    id: str
    question: str
    action: str
    confidence: float
    created_at: str
    outcome: float | None = None
    notes: str = ""

@dataclass
class AgentScore:
    agent: str
    predictions: int = 0
    correct: int = 0

    @property
    def accuracy(self) -> float | None:
        return self.correct / self.predictions if self.predictions else None

class PerformanceMemory:
    def __init__(self) -> None:
        self.decisions: dict[str, DecisionRecord] = {}
        self.agent_scores: dict[str, AgentScore] = {}

    def record_decision(self, question: str, action: str, confidence: float) -> DecisionRecord:
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        record = DecisionRecord(
            id=str(uuid.uuid4()), question=question, action=action.upper(),
            confidence=confidence,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.decisions[record.id] = record
        return record

    def record_outcome(self, decision_id: str, outcome: float, notes: str = "") -> DecisionRecord:
        if decision_id not in self.decisions:
            raise KeyError("Unknown decision")
        record = self.decisions[decision_id]
        record.outcome, record.notes = float(outcome), notes
        return record

    def record_agent_result(self, agent: str, correct: bool) -> AgentScore:
        score = self.agent_scores.setdefault(agent, AgentScore(agent=agent))
        score.predictions += 1
        score.correct += int(correct)
        return score

    def summary(self) -> dict[str, Any]:
        resolved = [d for d in self.decisions.values() if d.outcome is not None]
        return {
            "total_decisions": len(self.decisions),
            "resolved_decisions": len(resolved),
            "agent_accuracy": {
                name: score.accuracy for name, score in self.agent_scores.items()
            },
        }
