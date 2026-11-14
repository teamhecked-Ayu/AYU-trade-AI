import pytest
from ayuai.debate.debate_engine import DebateEngine
from ayuai.reasoning.models import ReasoningReport, Contradiction

class FakeManager:
    async def analyze_all_detailed(self, prompt, system_prompt=None):
        class Run:
            responses = []
        return Run()

@pytest.mark.asyncio
async def test_debate_surfaces_unresolved_contradictions():
    report = ReasoningReport(
        contradictions=[Contradiction(topic="buy vs wait")],
        evidence_gaps=["Conflicting evidence"],
    )
    result = await DebateEngine(FakeManager()).run("Should I act?", [], report)
    assert result.unresolved_issues
    assert result.rounds
