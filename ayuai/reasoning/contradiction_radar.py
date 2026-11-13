"""Find explicit conflicting conclusions without pretending semantic certainty."""
from __future__ import annotations
from ayuai.providers.base import ProviderResponse
from .models import Contradiction

OPPOSITES = (("buy", "sell"), ("buy", "wait"), ("proceed", "avoid"), ("increase", "decrease"), ("bullish", "bearish"))

class ContradictionRadar:
    def detect(self, responses: list[ProviderResponse]) -> list[Contradiction]:
        results: list[Contradiction] = []
        texts = {r.provider: r.content.lower() for r in responses}
        for left, right in OPPOSITES:
            left_providers = [name for name, text in texts.items() if left in text]
            right_providers = [name for name, text in texts.items() if right in text]
            if left_providers and right_providers:
                positions = {name: left for name in left_providers}
                positions.update({name: right for name in right_providers})
                results.append(Contradiction(
                    topic=f"Conflicting positions: {left} vs {right}",
                    positions=positions,
                    severity="high" if len(positions) >= 3 else "moderate",
                ))
        return results
