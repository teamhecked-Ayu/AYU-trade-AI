"""Independent analysis stage without group influence."""
from ayuai.providers.provider_manager import ProviderManager
from ayuai.providers.base import ProviderResponse

INDEPENDENT_REASONING_PROMPT = """You are one independent analyst inside AYUAI.
Analyze the user's task without assuming other agents agree with you.
Do not imitate a majority view. Clearly separate facts, assumptions, risks,
uncertainties, and your conclusion.

Return:
1. CONCLUSION
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

    async def run(self, user_task: str) -> list[ProviderResponse]:
        return await self.provider_manager.analyze_all(
            user_task, system_prompt=INDEPENDENT_REASONING_PROMPT
        )
