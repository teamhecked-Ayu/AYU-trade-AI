from ayuai.decision.decision_engine import DecisionEngine
from ayuai.reasoning.models import ReasoningReport
from ayuai.debate.models import DebateReport


def test_only_explicit_conclusion_field_counts_as_action():
    analyses = [
        {
            "provider": "provider-a",
            "content": (
                "The report discusses SELL as a rejected alternative.\n"
                "CONCLUSION: BUY\n"
                "Risks: a sudden SELL signal would invalidate this view."
            ),
        }
    ]

    assert DecisionEngine()._actions(analyses) == ["BUY"]


def test_conclusion_heading_on_own_line_is_supported():
    analyses = [{"content": "1. CONCLUSION\n- HOLD\nKEY CLAIMS\nBUY is not supported."}]
    assert DecisionEngine()._actions(analyses) == ["HOLD"]


def test_action_mentioned_without_conclusion_is_ignored():
    analyses = [
        {"content": "BUY is one possible view, but the evidence does not support it."},
        {"content": "Do not SELL based on this report."},
    ]
    assert DecisionEngine()._actions(analyses) == []


def test_negated_or_explanatory_conclusion_is_ignored():
    analyses = [
        {"content": "CONCLUSION: DO NOT BUY"},
        {"content": "CONCLUSION: I would WAIT for more evidence"},
    ]
    assert DecisionEngine()._actions(analyses) == []


def test_multiple_conclusion_fields_are_treated_as_ambiguous():
    analyses = [
        {"content": "CONCLUSION: BUY\nCONCLUSION: SELL"}
    ]
    assert DecisionEngine()._actions(analyses) == []


def test_tied_actions_produce_insufficient_evidence_and_require_review():
    analyses = [
        {"content": "CONCLUSION: BUY"},
        {"content": "CONCLUSION: SELL"},
    ]

    result = DecisionEngine().decide(analyses, ReasoningReport(), DebateReport())

    assert result.conclusion == "INSUFFICIENT EVIDENCE"
    assert result.confidence == 0
    assert result.requires_human_review is True
    assert result.status == "review_required"
    assert any("tied" in item.lower() for item in result.rationale)


def test_clear_consensus_still_calculates_confidence():
    analyses = [
        {"content": "CONCLUSION: WAIT"},
        {"content": "CONCLUSION: WAIT"},
        {"content": "CONCLUSION: WAIT"},
    ]

    result = DecisionEngine().decide(analyses, ReasoningReport(), DebateReport())

    assert result.conclusion == "WAIT"
    assert result.confidence == 1
    assert result.requires_human_review is False


def test_missing_conclusions_return_insufficient_evidence():
    result = DecisionEngine().decide(
        [{"content": "BUY is discussed, but nothing is concluded."}],
        ReasoningReport(),
        DebateReport(),
    )

    assert result.conclusion == "INSUFFICIENT EVIDENCE"
    assert result.confidence == 0
    assert result.requires_human_review is True
