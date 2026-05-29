import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.config import settings
from app.intake.validator import validate_router_output

Intent = Literal[
    "warranty_replacement_request",
    "warranty_policy_question",
    "unknown",
]
RoutingStatus = Literal[
    "routed",
    "clarification_required",
    "not_routed",
    "fallback_routed",
    "fallback_clarification_required",
    "fallback_not_routed",
    "llm_failed_fallback",
    "validation_failed_fallback",
]


class IntakeRouterOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: Intent
    confidence: float | None = Field(default=None, ge=0, le=1)
    product_type: str | None = None
    product_issue: str | None = None
    damage_type: str | None = None
    customer_id: str | None = None
    order_id: str | None = None
    requires_order_lookup: bool = False
    requires_policy_lookup: bool = False
    requires_clarification: bool = False
    missing_fields: list[str] = Field(default_factory=list)
    next_question: str | None = None
    routed_workflow: Literal["warranty_replacement"] | None = None
    can_start_workflow: bool = False
    routing_status: RoutingStatus
    error_message: str | None = None


INTAKE_ROUTER_INSTRUCTIONS = """
You classify a customer message for a governed workflow router.
Return JSON only, with these keys:
intent, confidence, product_type, product_issue, damage_type, customer_id,
order_id, requires_order_lookup, requires_policy_lookup,
requires_clarification, missing_fields, next_question, routed_workflow,
routing_status, error_message.

Allowed intents: warranty_replacement_request, warranty_policy_question, unknown.
Allowed routed_workflow: warranty_replacement or null.

The router interprets and routes only. It must not decide eligibility, approve
requests, create replacement requests, override guardrails, or claim business
actions were allowed.
""".strip()


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _next_question(missing_fields: list[str]) -> str | None:
    if not missing_fields:
        return None
    labels = {
        "customer_id": "customer ID",
        "order_id": "order ID",
        "product_type": "product type",
    }
    friendly = [labels.get(field, field) for field in missing_fields]
    if len(friendly) == 1:
        return f"Please provide your {friendly[0]} so I can route this request."
    return f"Please provide your {', '.join(friendly[:-1])}, and {friendly[-1]} so I can route this request."


def _extract_identifier(message: str, label: str) -> str | None:
    patterns = [
        rf"\b{label}\s*(?:id|number|#)?\s*(?:is|=|:)?\s*([A-Za-z0-9_-]+)",
        rf"\b{label}[_\s-]*id\s*(?:is|=|:)?\s*([A-Za-z0-9_-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip().strip(".,;:")
    return None


def _extract_identifiers(message: str) -> dict[str, str | None]:
    return {
        "customer_id": _extract_identifier(message, "customer"),
        "order_id": _extract_identifier(message, "order"),
    }


def _finalize_output(
    *,
    intent: Intent,
    confidence: float | None,
    product_type: str | None,
    product_issue: str | None,
    damage_type: str | None,
    customer_id: str | None,
    order_id: str | None,
    routing_prefix: Literal["", "fallback_"] = "",
    error_message: str | None = None,
) -> dict[str, Any]:
    missing_fields: list[str] = []
    requires_order_lookup = intent == "warranty_replacement_request"
    requires_policy_lookup = intent in {
        "warranty_replacement_request",
        "warranty_policy_question",
    }

    if intent == "warranty_replacement_request":
        if not customer_id:
            missing_fields.append("customer_id")
        if not order_id:
            missing_fields.append("order_id")

    requires_clarification = bool(missing_fields)
    routed_workflow = (
        "warranty_replacement"
        if intent == "warranty_replacement_request"
        else None
    )
    can_start_workflow = bool(routed_workflow) and not requires_clarification

    if requires_clarification:
        routing_status: RoutingStatus = (
            "fallback_clarification_required"
            if routing_prefix
            else "clarification_required"
        )
    elif intent == "unknown" or routed_workflow is None:
        routing_status = (
            "fallback_not_routed" if routing_prefix else "not_routed"
        )
    else:
        routing_status = "fallback_routed" if routing_prefix else "routed"

    output = IntakeRouterOutput(
        intent=intent,
        confidence=confidence,
        product_type=product_type,
        product_issue=product_issue,
        damage_type=damage_type,
        customer_id=customer_id,
        order_id=order_id,
        requires_order_lookup=requires_order_lookup,
        requires_policy_lookup=requires_policy_lookup,
        requires_clarification=requires_clarification,
        missing_fields=missing_fields,
        next_question=_next_question(missing_fields),
        routed_workflow=routed_workflow,
        can_start_workflow=can_start_workflow,
        routing_status=routing_status,
        error_message=error_message,
    ).model_dump()

    validation = validate_router_output(output)
    if validation["validation_status"] == "failed":
        fallback = _deterministic_route(
            message="",
            customer_id=customer_id,
            order_id=order_id,
            error_message="; ".join(validation["validation_errors"]),
        )
        fallback["routing_status"] = "validation_failed_fallback"
        return fallback
    return output


def _deterministic_route(
    message: str,
    customer_id: str | None,
    order_id: str | None,
    error_message: str | None = None,
) -> dict[str, Any]:
    normalized = message.lower()
    replacement_terms = [
        "replacement",
        "replace",
        "cracked",
        "broken",
        "damaged",
        "damage",
        "stopped powering",
        "won't power",
        "wont power",
    ]
    policy_terms = ["warranty", "covered", "cover", "policy"]

    if any(term in normalized for term in replacement_terms):
        intent: Intent = "warranty_replacement_request"
        confidence = 0.82
    elif any(term in normalized for term in policy_terms):
        intent = "warranty_policy_question"
        confidence = 0.7
    else:
        intent = "unknown"
        confidence = 0.35

    product_type = "laptop" if "laptop" in normalized else None
    product_issue = None
    damage_type = None
    if "cracked" in normalized and "screen" in normalized:
        product_issue = "cracked_screen"
        damage_type = "possible_accidental_damage"
    elif "screen" in normalized:
        product_issue = "screen_issue"
    elif "stopped powering" in normalized or "power" in normalized:
        product_issue = "power_issue"
        damage_type = "possible_manufacturing_defect"
    elif "damage" in normalized or "damaged" in normalized:
        product_issue = "damage_reported"
        damage_type = "unknown"

    return _finalize_output(
        intent=intent,
        confidence=confidence,
        product_type=product_type,
        product_issue=product_issue,
        damage_type=damage_type,
        customer_id=customer_id,
        order_id=order_id,
        routing_prefix="fallback_",
        error_message=error_message,
    )


def _extract_json_response(text: str | None) -> dict[str, Any]:
    if not text:
        raise ValueError("OpenAI response did not include output text.")
    return json.loads(text)


def _llm_route(
    message: str,
    customer_id: str | None,
    order_id: str | None,
) -> dict[str, Any]:
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.responses.create(
        model=settings.OPENAI_MODEL,
        instructions=INTAKE_ROUTER_INSTRUCTIONS,
        input=json.dumps(
            {
                "message": message,
                "explicit_customer_id": customer_id,
                "explicit_order_id": order_id,
            },
            sort_keys=True,
        ),
        temperature=0.0,
    )
    parsed = _extract_json_response(getattr(response, "output_text", None))
    parsed["customer_id"] = customer_id or _clean(parsed.get("customer_id"))
    parsed["order_id"] = order_id or _clean(parsed.get("order_id"))
    parsed.setdefault("error_message", None)

    finalized = _finalize_output(
        intent=parsed.get("intent", "unknown"),
        confidence=parsed.get("confidence"),
        product_type=_clean(parsed.get("product_type")),
        product_issue=_clean(parsed.get("product_issue")),
        damage_type=_clean(parsed.get("damage_type")),
        customer_id=parsed["customer_id"],
        order_id=parsed["order_id"],
    )
    validation = validate_router_output(finalized)
    if validation["validation_status"] == "failed":
        fallback = _deterministic_route(
            message,
            customer_id,
            order_id,
            error_message="; ".join(validation["validation_errors"]),
        )
        fallback["routing_status"] = "validation_failed_fallback"
        return fallback
    return finalized


def route_customer_message(
    message: str,
    customer_id: str | None = None,
    order_id: str | None = None,
) -> dict[str, Any]:
    cleaned_message = message.strip()
    extracted_ids = _extract_identifiers(cleaned_message)
    cleaned_customer_id = _clean(customer_id) or extracted_ids["customer_id"]
    cleaned_order_id = _clean(order_id) or extracted_ids["order_id"]

    if not cleaned_message:
        return _finalize_output(
            intent="unknown",
            confidence=0.0,
            product_type=None,
            product_issue=None,
            damage_type=None,
            customer_id=cleaned_customer_id,
            order_id=cleaned_order_id,
            routing_prefix="fallback_",
            error_message="Message is required.",
        )

    if not settings.OPENAI_API_KEY or not settings.OPENAI_MODEL:
        return _deterministic_route(
            cleaned_message,
            cleaned_customer_id,
            cleaned_order_id,
        )

    try:
        return _llm_route(cleaned_message, cleaned_customer_id, cleaned_order_id)
    except Exception as exc:
        return _deterministic_route(
            cleaned_message,
            cleaned_customer_id,
            cleaned_order_id,
            error_message=f"LLM intake unavailable; deterministic fallback used: {exc}",
        )
