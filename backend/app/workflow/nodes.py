from typing import Any

from app.tools.warranty_tools import (
    check_inventory_availability,
    check_replacement_eligibility,
    create_replacement_request,
    escalate_to_human,
    generate_customer_response,
    lookup_order,
    retrieve_warranty_policy,
    verify_identity,
)
from app.workflow.state import WarrantyWorkflowState


def _failure_reason(result: dict[str, Any], fallback: str) -> str:
    return str(result.get("reason") or result.get("message") or fallback)


def verify_identity_node(state: WarrantyWorkflowState) -> dict[str, Any]:
    result = verify_identity(state["customer_id"])
    identity_verified = bool(result.get("identity_verified"))
    updates: dict[str, Any] = {
        "identity_verified": identity_verified,
        "workflow_status": "identity_checked",
    }

    if not identity_verified:
        updates.update(
            {
                "escalation_required": True,
                "escalation_reason": _failure_reason(
                    result,
                    "Customer identity could not be verified.",
                ),
                "error_category": "identity_verification_failed",
            }
        )

    return updates


def lookup_order_node(state: WarrantyWorkflowState) -> dict[str, Any]:
    result = lookup_order(state["customer_id"], state["order_id"])
    if result.get("result_status") == "success":
        return {
            "product_id": result["product_id"],
            "product_family": result["product_family"],
            "order_status": result["order_status"],
            "purchase_age_months": result["purchase_age_months"],
            "order_retrieved": True,
            "customer_authorized": True,
            "workflow_status": "order_retrieved",
        }

    return {
        "order_retrieved": False,
        "customer_authorized": result.get("result_status") != "authorization_error",
        "escalation_required": True,
        "escalation_reason": _failure_reason(
            result,
            "Order could not be retrieved or authorized.",
        ),
        "error_category": str(result.get("result_status") or "order_lookup_failed"),
        "workflow_status": "order_lookup_failed",
    }


def retrieve_warranty_policy_node(state: WarrantyWorkflowState) -> dict[str, Any]:
    product_family = state.get("product_family")
    if not product_family:
        return {
            "escalation_required": True,
            "escalation_reason": "Product family is required to retrieve warranty policy.",
            "error_category": "missing_product_family",
            "workflow_status": "policy_lookup_failed",
        }

    result = retrieve_warranty_policy(product_family, region="US")
    if result.get("result_status") == "success":
        return {
            "policy_id": result["policy_id"],
            "policy_reference": result["policy_reference"],
            "policy_version": result["version"],
            "workflow_status": "policy_retrieved",
        }

    return {
        "escalation_required": True,
        "escalation_reason": _failure_reason(
            result,
            "Current warranty policy could not be retrieved.",
        ),
        "error_category": str(result.get("result_status") or "policy_lookup_failed"),
        "workflow_status": "policy_lookup_failed",
    }


def check_replacement_eligibility_node(
    state: WarrantyWorkflowState,
) -> dict[str, Any]:
    policy_id = state.get("policy_id")
    if not policy_id:
        return {
            "eligibility_status": "human_review_required",
            "escalation_required": True,
            "escalation_reason": "Policy ID is required to check replacement eligibility.",
            "error_category": "missing_policy_id",
            "workflow_status": "eligibility_check_failed",
        }

    result = check_replacement_eligibility(
        state["customer_id"],
        state["order_id"],
        policy_id,
    )
    eligibility_status = result.get("eligibility_status")
    reason = _failure_reason(result, "Replacement eligibility could not be determined.")
    updates: dict[str, Any] = {
        "eligibility_status": eligibility_status,
        "eligibility_reason": reason,
        "policy_reference": result.get("policy_reference", state.get("policy_reference")),
        "policy_version": result.get("policy_version", state.get("policy_version")),
        "workflow_status": "eligibility_checked",
    }

    if eligibility_status in {"unknown", "human_review_required"}:
        updates.update(
            {
                "escalation_required": True,
                "escalation_reason": reason,
                "error_category": "eligibility_requires_review",
            }
        )

    return updates


def check_inventory_availability_node(
    state: WarrantyWorkflowState,
) -> dict[str, Any]:
    product_id = state.get("product_id")
    if not product_id:
        return {
            "inventory_available": False,
            "inventory_status": "unavailable",
            "escalation_required": True,
            "escalation_reason": "Product ID is required to check inventory.",
            "error_category": "missing_product_id",
            "workflow_status": "inventory_check_failed",
        }

    result = check_inventory_availability(product_id)
    inventory_available = bool(result.get("inventory_available"))
    updates: dict[str, Any] = {
        "inventory_available": inventory_available,
        "inventory_status": result.get("inventory_status"),
        "workflow_status": "inventory_checked",
    }

    if not inventory_available:
        updates.update(
            {
                "escalation_required": True,
                "escalation_reason": _failure_reason(
                    result,
                    "Replacement inventory is unavailable.",
                ),
                "error_category": "inventory_unavailable",
            }
        )

    return updates


def guardrail_check_node(state: WarrantyWorkflowState) -> dict[str, Any]:
    allow_replacement = (
        state.get("identity_verified") is True
        and state.get("customer_authorized") is True
        and state.get("order_retrieved") is True
        and state.get("order_status") == "delivered"
        and bool(state.get("policy_reference"))
        and state.get("eligibility_status") == "eligible"
        and state.get("inventory_available") is True
        and state.get("escalation_required") is False
    )

    if allow_replacement:
        return {
            "guardrail_decision": "allow",
            "workflow_status": "guardrail_allowed",
        }

    if state.get("eligibility_status") == "not_eligible":
        return {
            "guardrail_decision": "block",
            "eligibility_reason": state.get("eligibility_reason")
            or "Replacement is not eligible under the current warranty policy.",
            "workflow_status": "guardrail_blocked",
        }

    return {
        "guardrail_decision": "escalate",
        "escalation_required": True,
        "escalation_reason": state.get("escalation_reason")
        or state.get("eligibility_reason")
        or "Replacement creation guardrail requires human review.",
        "workflow_status": "guardrail_escalated",
    }


def create_replacement_request_node(
    state: WarrantyWorkflowState,
) -> dict[str, Any]:
    if state.get("guardrail_decision") != "allow":
        return {
            "replacement_request_id": None,
            "replacement_status": "not_created",
            "workflow_status": "replacement_not_created",
        }

    result = create_replacement_request(
        customer_id=state["customer_id"],
        order_id=state["order_id"],
        product_id=state.get("product_id") or "",
        eligibility_status=state.get("eligibility_status") or "unknown",
        inventory_available=bool(state.get("inventory_available")),
    )
    if result.get("result_status") == "success":
        return {
            "replacement_request_id": result["replacement_request_id"],
            "replacement_status": result["replacement_status"],
            "workflow_status": "replacement_created",
        }

    return {
        "replacement_request_id": None,
        "replacement_status": result.get("replacement_status", "not_created"),
        "guardrail_decision": "block",
        "eligibility_reason": _failure_reason(
            result,
            "Replacement request was blocked by tool guardrails.",
        ),
        "workflow_status": "replacement_not_created",
    }


def escalate_to_human_node(state: WarrantyWorkflowState) -> dict[str, Any]:
    reason = (
        state.get("escalation_reason")
        or state.get("eligibility_reason")
        or "Workflow requires human review."
    )
    result = escalate_to_human(
        customer_id=state["customer_id"],
        order_id=state["order_id"],
        reason=reason,
    )
    return {
        "escalation_id": result.get("escalation_id"),
        "escalation_required": True,
        "escalation_reason": reason,
        "workflow_status": "escalated",
    }


def generate_customer_response_node(
    state: WarrantyWorkflowState,
) -> dict[str, Any]:
    reason = (
        state.get("escalation_reason")
        or state.get("eligibility_reason")
        or "Warranty workflow completed."
    )
    result = generate_customer_response(
        eligibility_status=state.get("eligibility_status") or "unknown",
        replacement_request_id=state.get("replacement_request_id"),
        escalation_id=state.get("escalation_id"),
        reason=reason,
    )
    return {
        "customer_response": result["customer_response"],
        "response_type": result["response_type"],
        "workflow_status": "completed",
    }
