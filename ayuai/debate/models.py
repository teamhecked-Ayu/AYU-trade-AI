from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class DebateRound:
    round_number: int
    prompt: str
    responses: dict[str, str] = field(default_factory=dict)

@dataclass
class DebateReport:
    rounds: list[DebateRound] = field(default_factory=list)
    unresolved_issues: list[str] = field(default_factory=list)
    minority_positions: dict[str, str] = field(default_factory=dict)
    status: str = "completed"
