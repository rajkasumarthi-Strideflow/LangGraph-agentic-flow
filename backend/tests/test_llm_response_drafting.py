from app.config import settings
from app.llm.response_drafter import (
    build_response_drafting_payload,
    draft_customer_response_with_llm,
)
from app.llm.response_validator import validate_llm_customer_response


def _state() -> dict:
    return {
        "customer_request": "My laptop screen cracked after 9 months. Can I get a replacement?",
        "customer_id": "cust_primary_001",
        "order_id": "ord_laptop_001",
        "eligibility_status": "not_eligible",
        "eligibility_reason": "Accidental damage and cracked screens are excluded.",
        "policy_reference": "pol_laptop_us_current_v2#v2.0",
        "policy_version": "2.0",
        "guardrail_decision": "block",
        "replacement_request_id": None,
        "escalation_id": None,
        "escalation_reason": None,
        "workflow_status": "completed",
        "payment_last_four": "1111",
        "deprecated_policy_content": "Old FAQ says cracked screens may be covered.",
    }


def test_build_response_drafting_payload_is_minimized() -> None:
    payload = build_response_drafting_payload(_state())

    assert set(payload) == {
        "customer_request",
        "eligibility_status",
        "eligibility_reason",
        "policy_reference",
        "policy_version",
        "guardrail_decision",
        "replacement_request_id",
        "escalation_id",
        "escalation_reason",
        "workflow_status",
    }
    assert "customer_id" not in payload
    assert "payment_last_four" not in payload
    assert "deprecated_policy_content" not in payload


def test_validator_passes_safe_not_eligible_response() -> None:
    result = validate_llm_customer_response(
        _state(),
        "Based on the current policy, this item is not automatically eligible for replacement because accidental damage is excluded.",
    )

    assert result["validation_status"] == "passed"
    assert result["validation_errors"] == []


def test_validator_fails_replacement_claim_without_request_id() -> None:
    result = validate_llm_customer_response(
        _state(),
        "Your replacement request has been created and shipment is on the way.",
    )

    assert result["validation_status"] == "failed"
    assert result["validation_errors"]


def test_validator_fails_eligible_claim_when_not_eligible() -> None:
    result = validate_llm_customer_response(
        _state(),
        "You are eligible for a warranty replacement.",
    )

    assert result["validation_status"] == "failed"
    assert result["validation_errors"]


def test_draft_customer_response_with_llm_returns_not_configured(
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)
    monkeypatch.setattr(settings, "OPENAI_MODEL", None)

    result = draft_customer_response_with_llm(_state())

    assert result["drafting_status"] == "not_configured"
    assert result["llm_customer_response"] is None
    assert result["usage"]["input_tokens"] is None
