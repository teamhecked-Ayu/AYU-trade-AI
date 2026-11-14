from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class FinalDecision:
    conclusion: str
    confidence: float
    confidence_label: str
    rationale: list[str] = field(default_factory=list)
    key_risks: list[str] = field(default_factory=list)
    unresolved_issues: list[str] = field(default_factory=list)
    minority_positions: dict[str, str] = field(default_factory=dict)
    requires_human_review: bool = False
    status: str = "ready"
