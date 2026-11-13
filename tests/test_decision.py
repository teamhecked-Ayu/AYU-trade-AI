from ayuai.decision.decision_engine import DecisionEngine
from ayuai.reasoning.models import ReasoningReport, Contradiction
from ayuai.debate.models import DebateReport

def test_conflicting_evidence_requires_review():
    analyses = [
        {"content": "CONCLUSION\nBUY"},
        {"content": "CONCLUSION\nBUY"},
        {"content": "CONCLUSION\nSELL"},
    ]
    reasoning = ReasoningReport(contradictions=[Contradiction(topic="buy vs sell")])
    decision = DecisionEngine().decide(analyses, reasoning, DebateReport())
    assert decision.conclusion == "BUY"
    assert decision.requires_human_review is True

def test_clear_agreement_can_be_ready():
    analyses = [{"content": "BUY"} for _ in range(5)]
    decision = DecisionEngine().decide(analyses, ReasoningReport(), DebateReport())
    assert decision.conclusion == "BUY"
    assert decision.requires_human_review is False
