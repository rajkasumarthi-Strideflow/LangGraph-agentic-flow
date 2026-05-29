from typing import Any

ALLOWED_INTENTS = {
    "warranty_replacement_request",
    "warranty_policy_question",
    "unknown",
}
ALLOWED_ROUTED_WORKFLOWS = {None, "warranty_replacement"}
FORBIDDEN_ROUTER_FIELDS = {
    "eligibility_status",
    "guardrail_decision",
    "replacement_request_id",
}
FORBIDDEN_APPROVAL_PHRASES = [
    "approved",
    "eligible for replacement",
    "replacement created",
    "replacement request created",
    "guardrail allowed",
]


def validate_router_output(output: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []

    intent = output.get("intent")
    if intent not in ALLOWED_INTENTS:
        errors.append(f"Unsupported intent: {intent}.")

    confidence = output.get("confidence")
    if confidence is not None and not 0 <= confidence <= 1:
        errors.append("Confidence must be between 0 and 1.")

    routed_workflow = output.get("routed_workflow")
    if routed_workflow not in ALLOWED_ROUTED_WORKFLOWS:
        errors.append(f"Unsupported routed_workflow: {routed_workflow}.")

    for field in FORBIDDEN_ROUTER_FIELDS:
        if field in output:
            errors.append(f"Router must not set {field}.")

    searchable_values = [
        str(value).lower()
        for value in output.values()
        if isinstance(value, str)
    ]
    for phrase in FORBIDDEN_APPROVAL_PHRASES:
        if any(phrase in value for value in searchable_values):
            errors.append("Router output must not claim action approval.")
            break

    return {
        "validation_status": "failed" if errors else "passed",
        "validation_errors": errors,
    }
