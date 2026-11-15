"""Independent analysis stage that preserves partial provider failures."""

from ayuai.providers.provider_manager import ProviderManager, ProviderRun
from ayuai.providers.base import ProviderResponse

INDEPENDENT_REASONING_PROMPT = """You are one independent analyst inside AYUAI.
Analyze the user's task without assuming other agents agree with you.
Do not imitate a majority view. Clearly separate facts, assumptions, risks,
uncertainties, and your conclusion.

Return the conclusion in exactly one explicit field:
CONCLUSION: BUY
Replace BUY with exactly one of: BUY, SELL, WAIT, HOLD, AVOID.
If the evidence does not support one of those actions, write:
CONCLUSION: INSUFFICIENT EVIDENCE
Do not put a directional action in the CONCLUSION field when you are uncertain.
Mention rejected actions only in the explanation, not in the CONCLUSION field.

Then return:
2. KEY CLAIMS
3. EVIDENCE OR REASONING
4. ASSUMPTIONS
5. RISKS
6. UNCERTAINTIES
7. CONFIDENCE (Low, Moderate, or High)
"""


class IndependentAnalysisAgent:
    def __init__(self, provider_manager: ProviderManager) -> None:
        self.provider_manager = provider_manager

    async def run_detailed(self, user_task: str) -> ProviderRun:
        """Return both successful analyses and sanitized failures."""
        return await self.provider_manager.analyze_all_detailed(
            user_task,
            system_prompt=INDEPENDENT_REASONING_PROMPT,
        )

    async def run(self, user_task: str) -> list[ProviderResponse]:
        result = await self.run_detailed(user_task)
        if not result.responses:
            raise RuntimeError("All configured AI providers failed.")
        return result.responses
