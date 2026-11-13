"""Step 5: deterministic synthesis of AYUAI evidence and debate results."""
from __future__ import annotations
import re
from collections import Counter
from ayuai.reasoning.models import ReasoningReport
from ayuai.debate.models import DebateReport
from .models import FinalDecision

class DecisionEngine:
    ACTIONS = ("BUY", "SELL", "WAIT", "HOLD", "AVOID")

    def _actions(self, analyses: list[dict]) -> list[str]:
        found = []
        for item in analyses:
            text = item.get("content", "").upper()
            match = re.search(r"\b(BUY|SELL|WAIT|HOLD|AVOID)\b", text)
            if match:
                found.append(match.group(1))
        return found

    def decide(self, analyses: list[dict], reasoning: ReasoningReport, debate: DebateReport) -> FinalDecision:
        actions = self._actions(analyses)
        counts = Counter(actions)
        conclusion = counts.most_common(1)[0][0] if counts else "INSUFFICIENT EVIDENCE"

        total = max(len(analyses), 1)
        agreement = counts.get(conclusion, 0) / total
        contradiction_penalty = min(0.35, 0.08 * len(reasoning.contradictions))
        gap_penalty = min(0.25, 0.05 * len(reasoning.evidence_gaps))
        failure_penalty = 0.20 if debate.status == "failed" else 0.0
        confidence = max(0.0, min(1.0, agreement - contradiction_penalty - gap_penalty - failure_penalty))

        if confidence >= 0.75:
            label = "high"
        elif confidence >= 0.45:
            label = "moderate"
        else:
            label = "low"

        risks = []
        for provider_risks in reasoning.risks.values():
            risks.extend(provider_risks)
        risks = list(dict.fromkeys(risks))[:10]

        unresolved = list(dict.fromkeys(
            reasoning.evidence_gaps + debate.unresolved_issues
        ))[:10]

        rationale = [
            f"{counts.get(conclusion, 0)} of {total} independent analyses contained the leading action signal: {conclusion}.",
            f"{len(reasoning.agreements)} multi-provider agreements and {len(reasoning.contradictions)} detected contradictions were considered.",
        ]
        if debate.rounds:
            rationale.append(f"{len(debate.rounds)} adversarial debate round(s) completed.")
        if conclusion == "INSUFFICIENT EVIDENCE":
            rationale.append("No clear action signal was extracted from the available analyses.")

        requires_review = (
            confidence < 0.45
            or bool(reasoning.contradictions)
            or debate.status != "completed"
            or conclusion == "INSUFFICIENT EVIDENCE"
        )

        return FinalDecision(
            conclusion=conclusion,
            confidence=round(confidence, 3),
            confidence_label=label,
            rationale=rationale,
            key_risks=risks,
            unresolved_issues=unresolved,
            minority_positions=debate.minority_positions,
            requires_human_review=requires_review,
            status="review_required" if requires_review else "ready",
        )
