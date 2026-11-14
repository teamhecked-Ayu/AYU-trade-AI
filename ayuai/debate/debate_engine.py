"""Step 4: structured adversarial review of independent AI analyses."""
from __future__ import annotations
from ayuai.providers.provider_manager import ProviderManager
from ayuai.reasoning.models import ReasoningReport
from .models import DebateRound, DebateReport
from .prompts import DEBATE_SYSTEM_PROMPT

class DebateEngine:
    def __init__(self, provider_manager: ProviderManager, max_rounds: int = 2) -> None:
        self.provider_manager = provider_manager
        self.max_rounds = max(1, min(max_rounds, 3))

    @staticmethod
    def _issues(reasoning: ReasoningReport) -> list[str]:
        issues = [c.topic for c in reasoning.contradictions]
        issues.extend(reasoning.evidence_gaps)
        return list(dict.fromkeys(issues))[:6]

    async def run(self, question: str, analyses: list[dict], reasoning: ReasoningReport) -> DebateReport:
        issues = self._issues(reasoning)
        report = DebateReport(unresolved_issues=list(issues))
        if not issues:
            return report

        # Only a compact evidence packet is shared. Agents cannot silently overwrite
        # the original independent analyses.
        packet = "\n".join(
            f"[{item['provider']}] {item['content'][:1800]}"
            for item in analyses
        )

        for round_number in range(1, self.max_rounds + 1):
            prompt = (
                f"QUESTION:\n{question}\n\n"
                f"UNRESOLVED ISSUES:\n" + "\n".join(f"- {x}" for x in issues) +
                f"\n\nINDEPENDENT ANALYSES:\n{packet}\n\n"
                "TASK: Challenge the weakest claims, identify unsupported assumptions, "
                "and state which position currently has stronger evidence. "
                "Do not vote based on provider identity."
            )
            run = await self.provider_manager.analyze_all_detailed(
                prompt, system_prompt=DEBATE_SYSTEM_PROMPT
            )
            responses = {r.provider: r.content for r in run.responses}
            report.rounds.append(DebateRound(round_number=round_number, prompt=prompt, responses=responses))

            if not responses:
                report.status = "failed"
                break

            # A second round focuses only on remaining disagreements.
            if round_number < self.max_rounds:
                issues = issues[:3]

        # Preserve dissent instead of deleting minority views.
        if report.rounds:
            last = report.rounds[-1].responses
            for provider, content in last.items():
                lowered = content.lower()
                if any(token in lowered for token in ("minority", "disagree", "insufficient evidence")):
                    report.minority_positions[provider] = content[:800]
        return report
