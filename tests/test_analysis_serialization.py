from ayuai.debate.models import DebateReport, DebateRound
from ayuai.decision.models import FinalDecision
from ayuai.orchestrator import AnalysisResult
from ayuai.reasoning.models import Claim, ReasoningReport
from ayuai.jobs.serialization import serialize_analysis_result


def test_analysis_payload_contains_dashboard_data_and_omits_internal_prompts():
    result = AnalysisResult(
        question="Explain a sample question",
        analyses=[{
            "provider": "provider-a",
            "model": "model-a",
            "content": "Independent analysis text",
            "metadata": {"request_id": "not-required"},
        }],
        reasoning=ReasoningReport(
            agreements=[Claim(text="A shared claim", providers=["provider-a"], support_count=1)]
        ),
        debate=DebateReport(
            rounds=[DebateRound(
                round_number=1,
                prompt="INTERNAL PROMPT SHOULD NOT BE RETURNED",
                responses={"provider-a": "A challenge response"},
            )],
            unresolved_issues=["Evidence gap"],
        ),
        decision=FinalDecision(
            conclusion="INSUFFICIENT EVIDENCE",
            confidence=0.2,
            confidence_label="low",
            rationale=["More evidence is needed."],
            key_risks=["Data may be incomplete."],
            requires_human_review=True,
            status="review_required",
        ),
        decision_id="decision-123",
        stage="final_decision",
    )

    payload = serialize_analysis_result(result)

    assert payload["provider_count"] == 1
    assert payload["analyses"][0]["content"] == "Independent analysis text"
    assert payload["reasoning"]["agreements"][0]["text"] == "A shared claim"
    assert payload["debate"]["rounds"][0]["responses"]["provider-a"] == "A challenge response"
    assert payload["decision"]["requires_human_review"] is True
    assert "prompt" not in payload["debate"]["rounds"][0]
    assert "INTERNAL PROMPT" not in str(payload)
