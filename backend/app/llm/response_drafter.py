import json
from typing import Any

from app.config import settings
from app.llm.usage import extract_usage

MINIMIZED_RESPONSE_FIELDS = [
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
]

RESPONSE_DRAFTING_INSTRUCTIONS = """
You are drafting a concise, polite, customer-safe support response.
You must not change the business decision.
You must not claim a replacement was created unless replacement_request_id exists.
You must not promise eligibility if eligibility_status is not eligible.
You must not expose internal policy wording beyond a customer-safe explanation.
You must not mention implementation details like LangGraph, guardrails, Postgres, audit logs, or tool calls.
Use only the structured payload provided. Do not infer extra facts.
""".strip()


def build_response_drafting_payload(state: dict) -> dict:
    return {field: state.get(field) for field in MINIMIZED_RESPONSE_FIELDS}


def _empty_result(
    drafting_status: str,
    payload: dict,
    error_message: str | None = None,
) -> dict[str, Any]:
    return {
        "drafting_status": drafting_status,
        "llm_customer_response": None,
        "model_name": None,
        "llm_input_payload": payload,
        "usage": {
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "cached_tokens": None,
        },
        "error_message": error_message,
    }


def draft_customer_response_with_llm(state: dict) -> dict[str, Any]:
    payload = build_response_drafting_payload(state)

    if not settings.LLM_RESPONSE_DRAFTING_ENABLED:
        return _empty_result("disabled", payload)

    if not settings.OPENAI_API_KEY or not settings.OPENAI_MODEL:
        return _empty_result("not_configured", payload)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.responses.create(
            model=settings.OPENAI_MODEL,
            instructions=RESPONSE_DRAFTING_INSTRUCTIONS,
            input=(
                "Draft the final customer response from this approved workflow state:\n"
                f"{json.dumps(payload, sort_keys=True)}"
            ),
            temperature=0.2,
        )
        return {
            "drafting_status": "completed",
            "llm_customer_response": getattr(response, "output_text", None),
            "model_name": settings.OPENAI_MODEL,
            "llm_input_payload": payload,
            "usage": extract_usage(response),
            "error_message": None,
        }
    except Exception as exc:
        return _empty_result("failed", payload, error_message=str(exc))
