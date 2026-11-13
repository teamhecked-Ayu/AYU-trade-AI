"""Deterministic first-pass extraction from the AYUAI response contract."""
from __future__ import annotations
import re
from collections import defaultdict
from ayuai.providers.base import ProviderResponse
from .models import Claim, ReasoningReport

HEADERS = ("CONCLUSION", "KEY CLAIMS", "EVIDENCE OR REASONING", "ASSUMPTIONS", "RISKS", "UNCERTAINTIES", "CONFIDENCE")

def _sections(content: str) -> dict[str, list[str]]:
    current = ""
    output: dict[str, list[str]] = defaultdict(list)
    for raw in content.splitlines():
        line = raw.strip()
        normalized = re.sub(r"^[#\-\d.\s]+", "", line).upper().rstrip(":")
        if normalized in HEADERS:
            current = normalized
            continue
        if current and line:
            output[current].append(re.sub(r"^[\-•*\d.\s]+", "", line).strip())
    return output

class ClaimExtractor:
    def analyze(self, responses: list[ProviderResponse]) -> ReasoningReport:
        report = ReasoningReport()
        claims: dict[str, Claim] = {}
        conclusions: dict[str, list[str]] = defaultdict(list)

        for response in responses:
            sections = _sections(response.content)
            provider = response.provider
            report.assumptions[provider] = sections.get("ASSUMPTIONS", [])
            report.risks[provider] = sections.get("RISKS", [])
            report.uncertainties[provider] = sections.get("UNCERTAINTIES", [])

            for claim_text in sections.get("KEY CLAIMS", []):
                key = " ".join(claim_text.lower().split())
                claim = claims.setdefault(key, Claim(text=claim_text))
                if provider not in claim.providers:
                    claim.providers.append(provider)
                    claim.support_count += 1

            conclusion = " ".join(sections.get("CONCLUSION", [])).strip()
            if conclusion:
                conclusions[conclusion.lower()].append(provider)

        for claim in claims.values():
            if claim.support_count >= 2:
                report.agreements.append(claim)
            else:
                report.disagreements.append(claim)

        # Similar conclusions with opposing action words are surfaced as evidence gaps.
        actions = {"buy", "sell", "wait", "hold", "proceed", "do not", "avoid"}
        found = {word for conclusion in conclusions for word in actions if word in conclusion}
        if len(found) > 1:
            report.evidence_gaps.append("Agents reached different action conclusions; further evidence review is required.")
        return report
