"""Convert analysis dataclasses into JSON-safe Celery result payloads."""

from __future__ import annotations

from dataclasses import asdict


def serialize_analysis_result(result) -> dict:
    """Return useful analysis detail without internal debate prompts or secrets."""
    debate = result.debate
    return {
        "status": "completed",
        "stage": result.stage,
        "question": result.question,
        "decision_id": result.decision_id,
        "decision": asdict(result.decision) if result.decision else None,
        "provider_count": len(result.analyses),
        "expected_provider_count": result.expected_provider_count or len(result.analyses),
        "provider_failures": result.provider_failures,
        "analyses": [
            {
                "provider": item["provider"],
                "model": item["model"],
                "content": item["content"],
            }
            for item in result.analyses
        ],
        "reasoning": asdict(result.reasoning) if result.reasoning else None,
        "debate": {
            "status": debate.status,
            "unresolved_issues": debate.unresolved_issues,
            "minority_positions": debate.minority_positions,
            "rounds": [
                {
                    "round_number": item.round_number,
                    "responses": item.responses,
                }
                for item in debate.rounds
            ],
        } if debate else None,
    }
