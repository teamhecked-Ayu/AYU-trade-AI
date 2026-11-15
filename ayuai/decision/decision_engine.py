"""Step 5: deterministic synthesis of explicitly labelled provider conclusions."""

from __future__ import annotations

import re
from collections import Counter

from ayuai.reasoning.models import ReasoningReport
from ayuai.debate.models import DebateReport
from .models import FinalDecision


class DecisionEngine:
    ACTIONS = ("BUY", "SELL", "WAIT", "HOLD", "AVOID")
    INSUFFICIENT = "INSUFFICIENT EVIDENCE"

    _CONCLUSION_LINE = re.compile(
        r"^\s*(?:\d+[.)]\s*)?(?:[-*]\s*)?"
        r"(?:\*\*|__)?CONCLUSION(?:\*\*|__)?[ \t]*"
        r"(?::[ \t]*|\n[ \t]*(?:[-*][ \t]*)?)"
        r"(?:\*\*|__)?(BUY|SELL|WAIT|HOLD|AVOID)\b",
        re.IGNORECASE | re.MULTILINE,
    )

    @classmethod
    def _explicit_action(cls, content: object) -> str | None:
        """Read exactly one action from an explicit CONCLUSION field.

        Mentions of actions in claims, risks, quotes, or rejected alternatives
        are deliberately ignored. Multiple conclusion fields are ambiguous.
        """
        if not isinstance(content, str):
            return None
        matches = cls._CONCLUSION_LINE.findall(content)
        if len(matches) != 1:
            return None
        action = matches[0].upper()
        return action if action in cls.ACTIONS else None

    def _actions(self, analyses: list[dict]) -> list[str]:
        found: list[str] = []
        for item in analyses:
            action = self._explicit_action(item.get("content"))
            if action:
                found.append(action)
        return found

    def decide(
        self,
        analyses: list[dict],
        reasoning: ReasoningReport,
        debate: DebateReport,
    ) -> FinalDecision:
        actions = self._actions(analyses)
        counts = Counter(actions)
        total = max(len(analyses), 1)

        highest_count = max(counts.values(), default=0)
        leaders = [action for action, count in counts.items() if count == highest_count]
        is_tied = len(leaders) > 1
        conclusion = leaders[0] if len(leaders) == 1 else self.INSUFFICIENT

        # A tie or an absence of a labelled conclusion is never converted into
        # a directional result. Confidence is zero until the evidence is clear.
        agreement = counts[conclusion] / total if conclusion in counts else 0.0
        contradiction_penalty = min(0.35, 0.08 * len(reasoning.contradictions))
        gap_penalty = min(0.25, 0.05 * len(reasoning.evidence_gaps))
        failure_penalty = 0.20 if debate.status == "failed" else 0.0
        coverage_penalty = (
            0.30 if len(actions) < 2
            else 0.10 if len(actions) < len(analyses)
            else 0.0
        )
        confidence = max(
            0.0,
            min(
                1.0,
                agreement
                - contradiction_penalty
                - gap_penalty
                - failure_penalty
                - coverage_penalty,
            ),
        )

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

        unresolved = list(
            dict.fromkeys(reasoning.evidence_gaps + debate.unresolved_issues)
        )[:10]

        rationale = [
            f"{counts.get(conclusion, 0)} of {total} independent analyses supported the leading conclusion: {conclusion}.",
            f"{len(actions)} provider(s) returned one unambiguous, labelled action conclusion.",
            f"{len(reasoning.agreements)} multi-provider agreements and {len(reasoning.contradictions)} detected contradictions were considered.",
        ]
        if debate.rounds:
            rationale.append(f"{len(debate.rounds)} adversarial debate round(s) completed.")
        if is_tied:
            rationale.append("The leading action signals are tied; no directional conclusion was selected.")
        elif conclusion == self.INSUFFICIENT:
            rationale.append("No unambiguous, explicitly labelled action conclusion was found.")

        requires_review = (
            confidence < 0.75
            or len(actions) < 2
            or len(actions) < len(analyses)
            or bool(reasoning.contradictions)
            or bool(reasoning.evidence_gaps)
            or bool(debate.unresolved_issues)
            or debate.status != "completed"
            or conclusion == self.INSUFFICIENT
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
