from app.observability.langsmith_tracing import traceable_if_enabled

FORBIDDEN_INTERNAL_TERMS = [
    "langgraph",
    "guardrail",
    "guardrails",
    "sqlalchemy",
    "railway",
    "postgres",
    "audit event",
    "tool call",
]

UNSUPPORTED_REPLACEMENT_CLAIMS = [
    "replacement was created",
    "replacement has been created",
    "replacement request was created",
    "replacement request has been created",
    "replacement has been processed",
    "replacement was processed",
    "shipment is on the way",
    "shipment has been created",
    "request has been approved",
    "replacement is approved",
    "replacement has been approved",
]


@traceable_if_enabled(name="validate_llm_customer_response")
def validate_llm_customer_response(
    state: dict,
    draft: str | None,
) -> dict[str, str | list[str]]:
    errors: list[str] = []
    normalized = (draft or "").strip().lower()

    if not normalized:
        return {
            "validation_status": "failed",
            "validation_errors": ["Draft response is empty."],
        }

    if not state.get("replacement_request_id"):
        for phrase in UNSUPPORTED_REPLACEMENT_CLAIMS:
            if phrase in normalized:
                errors.append(
                    "Draft claims replacement creation, approval, processing, or shipment without a replacement request.",
                )
                break

    if state.get("eligibility_status") == "not_eligible" and (
        "you are eligible" in normalized
        or "you're eligible" in normalized
        or "your item is eligible" in normalized
        or "covered for a replacement" in normalized
    ):
        errors.append("Draft says the customer is eligible despite not_eligible status.")

    if state.get("guardrail_decision") == "block" and (
        "action was allowed" in normalized
        or "we can create a replacement" in normalized
        or "we will create a replacement" in normalized
    ):
        errors.append("Draft implies a blocked action was allowed.")

    if not state.get("escalation_id") and (
        "routed for human review" in normalized
        or "escalated to a human" in normalized
        or "sent to a specialist" in normalized
    ):
        errors.append("Draft claims human escalation when no escalation exists.")

    for term in FORBIDDEN_INTERNAL_TERMS:
        if term in normalized:
            errors.append(f"Draft mentions internal implementation detail: {term}.")

    return {
        "validation_status": "failed" if errors else "passed",
        "validation_errors": errors,
    }
