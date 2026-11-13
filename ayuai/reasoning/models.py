"""Typed reasoning data used between AYUAI stages."""
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class Claim:
    text: str
    providers: list[str] = field(default_factory=list)
    support_count: int = 0
    challenge_count: int = 0

@dataclass
class Contradiction:
    topic: str
    positions: dict[str, str] = field(default_factory=dict)
    severity: str = "moderate"

@dataclass
class ReasoningReport:
    agreements: list[Claim] = field(default_factory=list)
    disagreements: list[Claim] = field(default_factory=list)
    contradictions: list[Contradiction] = field(default_factory=list)
    assumptions: dict[str, list[str]] = field(default_factory=dict)
    risks: dict[str, list[str]] = field(default_factory=dict)
    uncertainties: dict[str, list[str]] = field(default_factory=dict)
    evidence_gaps: list[str] = field(default_factory=list)
