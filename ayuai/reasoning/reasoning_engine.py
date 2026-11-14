"""Step 3: converts independent model responses into a structured reasoning map."""
from __future__ import annotations
from ayuai.providers.base import ProviderResponse
from .claim_extractor import ClaimExtractor
from .contradiction_radar import ContradictionRadar
from .models import ReasoningReport

class ReasoningEngine:
    def __init__(self) -> None:
        self.claim_extractor = ClaimExtractor()
        self.contradiction_radar = ContradictionRadar()

    def analyze(self, responses: list[ProviderResponse]) -> ReasoningReport:
        report = self.claim_extractor.analyze(responses)
        report.contradictions = self.contradiction_radar.detect(responses)
        if report.contradictions:
            report.evidence_gaps.append("Contradictory conclusions detected; do not finalize a decision yet.")
        if not report.agreements:
            report.evidence_gaps.append("No multi-provider claim agreement detected.")
        return report
