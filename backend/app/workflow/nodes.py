from typing import Any

from app.audit.events import AuditEventType
from app.audit.logger import log_node_event
from app.llm.response_drafter import draft_customer_response_with_llm
from app.llm.response_validator import validate_llm_customer_response
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

    log_node_event(
        state={**state, **updates},
        event_type=AuditEventType.IDENTITY_VERIFIED,
        node_name="verify_identity",
        tool_name="verify_identity",
        input_summary={"customer_id": state["customer_id"]},
        output_summary={
            "identity_verified": identity_verified,
            "result_status": result.get("result_status"),
        },
        reason=updates.get("escalation_reason") or result.get("reason"),
    )
    return updates


def lookup_order_node(state: WarrantyWorkflowState) -> dict[str, Any]:
    result = lookup_order(state["customer_id"], state["order_id"])
    if result.get("result_status") == "success":
        updates = {
            "product_id": result["product_id"],
            "product_family": result["product_family"],
            "order_status": result["order_status"],
            "purchase_age_months": result["purchase_age_months"],
            "order_retrieved": True,
            "customer_authorized": True,
            "workflow_status": "order_retrieved",
        }
        log_node_event(
            state={**state, **updates},
            event_type=AuditEventType.ORDER_LOOKUP_COMPLETED,
            node_name="lookup_order",
            tool_name="lookup_order",
            input_summary={
                "customer_id": state["customer_id"],
                "order_id": state["order_id"],
            },
            output_summary={
                "result_status": result.get("result_status"),
                "order_retrieved": True,
                "customer_authorized": True,
                "product_id": result["product_id"],
                "product_family": result["product_family"],
                "order_status": result["order_status"],
                "purchase_age_months": result["purchase_age_months"],
            },
        )
        return updates

    updates = {
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
    log_node_event(
        state={**state, **updates},
        event_type=AuditEventType.ORDER_LOOKUP_COMPLETED,
        node_name="lookup_order",
        tool_name="lookup_order",
        input_summary={
            "customer_id": state["customer_id"],
            "order_id": state["order_id"],
        },
        output_summary={
            "result_status": result.get("result_status"),
            "order_retrieved": False,
            "customer_authorized": updates["customer_authorized"],
        },
        reason=updates["escalation_reason"],
    )
    return updates


def retrieve_warranty_policy_node(state: WarrantyWorkflowState) -> dict[str, Any]:
    product_family = state.get("product_family")
    if not product_family:
        updates = {
            "escalation_required": True,
            "escalation_reason": "Product family is required to retrieve warranty policy.",
            "error_category": "missing_product_family",
            "workflow_status": "policy_lookup_failed",
        }
        log_node_event(
            state={**state, **updates},
            event_type=AuditEventType.POLICY_RETRIEVED,
            node_name="retrieve_warranty_policy",
            tool_name="retrieve_warranty_policy",
            input_summary={"product_family": None, "region": "US"},
            output_summary={"result_status": "missing_product_family"},
            reason=updates["escalation_reason"],
        )
        return updates

    result = retrieve_warranty_policy(product_family, region="US")
    if result.get("result_status") == "success":
        updates = {
            "policy_id": result["policy_id"],
            "policy_reference": result["policy_reference"],
            "policy_version": result["version"],
            "workflow_status": "policy_retrieved",
        }
        log_node_event(
            state={**state, **updates},
            event_type=AuditEventType.POLICY_RETRIEVED,
            node_name="retrieve_warranty_policy",
            tool_name="retrieve_warranty_policy",
            input_summary={"product_family": product_family, "region": "US"},
            output_summary={
                "result_status": result.get("result_status"),
                "policy_id": result["policy_id"],
                "policy_reference": result["policy_reference"],
                "policy_version": result["version"],
                "status": result["status"],
            },
        )
        return updates

    updates = {
        "escalation_required": True,
        "escalation_reason": _failure_reason(
            result,
            "Current warranty policy could not be retrieved.",
        ),
        "error_category": str(result.get("result_status") or "policy_lookup_failed"),
        "workflow_status": "policy_lookup_failed",
    }
    log_node_event(
        state={**state, **updates},
        event_type=AuditEventType.POLICY_RETRIEVED,
        node_name="retrieve_warranty_policy",
        tool_name="retrieve_warranty_policy",
        input_summary={"product_family": product_family, "region": "US"},
        output_summary={"result_status": result.get("result_status")},
        reason=updates["escalation_reason"],
    )
    return updates


def check_replacement_eligibility_node(
    state: WarrantyWorkflowState,
) -> dict[str, Any]:
    policy_id = state.get("policy_id")
    if not policy_id:
        updates = {
            "eligibility_status": "human_review_required",
            "escalation_required": True,
            "escalation_reason": "Policy ID is required to check replacement eligibility.",
            "error_category": "missing_policy_id",
            "workflow_status": "eligibility_check_failed",
        }
        log_node_event(
            state={**state, **updates},
            event_type=AuditEventType.ELIGIBILITY_CHECKED,
            node_name="check_replacement_eligibility",
            tool_name="check_replacement_eligibility",
            input_summary={
                "customer_id": state["customer_id"],
                "order_id": state["order_id"],
                "policy_id": None,
            },
            output_summary={"eligibility_status": "human_review_required"},
            reason=updates["escalation_reason"],
        )
        return updates

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

    log_node_event(
        state={**state, **updates},
        event_type=AuditEventType.ELIGIBILITY_CHECKED,
        node_name="check_replacement_eligibility",
        tool_name="check_replacement_eligibility",
        input_summary={
            "customer_id": state["customer_id"],
            "order_id": state["order_id"],
            "policy_id": policy_id,
        },
        output_summary={
            "result_status": result.get("result_status"),
            "eligibility_status": eligibility_status,
            "eligibility_reason": reason,
            "policy_reference": updates.get("policy_reference"),
            "policy_version": updates.get("policy_version"),
        },
        reason=reason,
    )
    return updates


def check_inventory_availability_node(
    state: WarrantyWorkflowState,
) -> dict[str, Any]:
    product_id = state.get("product_id")
    if not product_id:
        updates = {
            "inventory_available": False,
            "inventory_status": "unavailable",
            "escalation_required": True,
            "escalation_reason": "Product ID is required to check inventory.",
            "error_category": "missing_product_id",
            "workflow_status": "inventory_check_failed",
        }
        log_node_event(
            state={**state, **updates},
            event_type=AuditEventType.INVENTORY_CHECKED,
            node_name="check_inventory_availability",
            tool_name="check_inventory_availability",
            input_summary={"product_id": None},
            output_summary={
                "inventory_available": False,
                "inventory_status": "unavailable",
            },
            reason=updates["escalation_reason"],
        )
        return updates

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

    log_node_event(
        state={**state, **updates},
        event_type=AuditEventType.INVENTORY_CHECKED,
        node_name="check_inventory_availability",
        tool_name="check_inventory_availability",
        input_summary={"product_id": product_id},
        output_summary={
            "result_status": result.get("result_status"),
            "inventory_available": inventory_available,
            "inventory_status": result.get("inventory_status"),
            "available_quantity": result.get("available_quantity"),
        },
        reason=updates.get("escalation_reason"),
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
        updates = {
            "guardrail_decision": "allow",
            "workflow_status": "guardrail_allowed",
        }
        log_node_event(
            state={**state, **updates},
            event_type=AuditEventType.GUARDRAIL_DECISION,
            node_name="guardrail_check",
            input_summary={
                "eligibility_status": state.get("eligibility_status"),
                "inventory_available": state.get("inventory_available"),
                "escalation_required": state.get("escalation_required"),
            },
            output_summary={"guardrail_decision": "allow"},
            reason="All replacement creation guardrail conditions passed.",
        )
        return updates

    if state.get("eligibility_status") == "not_eligible":
        reason = (
            state.get("eligibility_reason")
            or "Replacement is not eligible under the current warranty policy."
        )
        updates = {
            "guardrail_decision": "block",
            "eligibility_reason": reason,
            "workflow_status": "guardrail_blocked",
        }
        log_node_event(
            state={**state, **updates},
            event_type=AuditEventType.GUARDRAIL_DECISION,
            node_name="guardrail_check",
            input_summary={
                "eligibility_status": state.get("eligibility_status"),
                "inventory_available": state.get("inventory_available"),
                "escalation_required": state.get("escalation_required"),
            },
            output_summary={
                "guardrail_decision": "block",
                "eligibility_reason": reason,
            },
            reason=reason,
        )
        return updates

    reason = (
        state.get("escalation_reason")
        or state.get("eligibility_reason")
        or "Replacement creation guardrail requires human review."
    )
    updates = {
        "guardrail_decision": "escalate",
        "escalation_required": True,
        "escalation_reason": reason,
        "workflow_status": "guardrail_escalated",
    }
    log_node_event(
        state={**state, **updates},
        event_type=AuditEventType.GUARDRAIL_DECISION,
        node_name="guardrail_check",
        input_summary={
            "eligibility_status": state.get("eligibility_status"),
            "inventory_available": state.get("inventory_available"),
            "escalation_required": state.get("escalation_required"),
        },
        output_summary={"guardrail_decision": "escalate"},
        reason=reason,
    )
    return updates


def create_replacement_request_node(
    state: WarrantyWorkflowState,
) -> dict[str, Any]:
    if state.get("guardrail_decision") != "allow":
        updates = {
            "replacement_request_id": None,
            "replacement_status": "not_created",
            "workflow_status": "replacement_not_created",
        }
        return updates

    result = create_replacement_request(
        customer_id=state["customer_id"],
        order_id=state["order_id"],
        product_id=state.get("product_id") or "",
        eligibility_status=state.get("eligibility_status") or "unknown",
        inventory_available=bool(state.get("inventory_available")),
    )
    if result.get("result_status") == "success":
        updates = {
            "replacement_request_id": result["replacement_request_id"],
            "replacement_status": result["replacement_status"],
            "workflow_status": "replacement_created",
        }
        log_node_event(
            state={**state, **updates},
            event_type=AuditEventType.REPLACEMENT_REQUEST_CREATED,
            node_name="create_replacement_request",
            tool_name="create_replacement_request",
            input_summary={
                "customer_id": state["customer_id"],
                "order_id": state["order_id"],
                "product_id": state.get("product_id"),
                "eligibility_status": state.get("eligibility_status"),
                "inventory_available": state.get("inventory_available"),
            },
            output_summary={
                "result_status": result.get("result_status"),
                "replacement_request_id": result["replacement_request_id"],
                "replacement_status": result["replacement_status"],
            },
        )
        return updates

    updates = {
        "replacement_request_id": None,
        "replacement_status": result.get("replacement_status", "not_created"),
        "guardrail_decision": "block",
        "eligibility_reason": _failure_reason(
            result,
            "Replacement request was blocked by tool guardrails.",
        ),
        "workflow_status": "replacement_not_created",
    }
    log_node_event(
        state={**state, **updates},
        event_type=AuditEventType.REPLACEMENT_REQUEST_CREATED,
        node_name="create_replacement_request",
        tool_name="create_replacement_request",
        input_summary={
            "customer_id": state["customer_id"],
            "order_id": state["order_id"],
            "product_id": state.get("product_id"),
            "eligibility_status": state.get("eligibility_status"),
            "inventory_available": state.get("inventory_available"),
        },
        output_summary={
            "result_status": result.get("result_status"),
            "replacement_status": updates["replacement_status"],
            "guardrail_decision": "block",
        },
        reason=updates["eligibility_reason"],
    )
    return updates


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
    updates = {
        "escalation_id": result.get("escalation_id"),
        "escalation_required": True,
        "escalation_reason": reason,
        "workflow_status": "escalated",
    }
    log_node_event(
        state={**state, **updates},
        event_type=AuditEventType.HUMAN_ESCALATION_CREATED,
        node_name="escalate_to_human",
        tool_name="escalate_to_human",
        input_summary={
            "customer_id": state["customer_id"],
            "order_id": state["order_id"],
        },
        output_summary={
            "result_status": result.get("result_status"),
            "escalation_id": result.get("escalation_id"),
            "escalation_status": result.get("escalation_status"),
        },
        reason=reason,
    )
    return updates


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
    deterministic_response = result["customer_response"]
    updates: dict[str, Any] = {
        "customer_response": result["customer_response"],
        "response_type": result["response_type"],
        "final_response_source": "deterministic",
        "workflow_status": "completed",
    }

    llm_result = draft_customer_response_with_llm({**state, **updates})
    usage = llm_result.get("usage") or {}
    llm_updates = {
        "llm_drafting_status": llm_result.get("drafting_status"),
        "llm_customer_response": llm_result.get("llm_customer_response"),
        "llm_model_name": llm_result.get("model_name"),
        "llm_input_tokens": usage.get("input_tokens"),
        "llm_output_tokens": usage.get("output_tokens"),
        "llm_total_tokens": usage.get("total_tokens"),
        "llm_cached_tokens": usage.get("cached_tokens"),
    }
    updates.update(llm_updates)

    drafting_status = llm_result.get("drafting_status")
    if drafting_status in {"disabled", "not_configured"}:
        source = (
            "llm_disabled_fallback"
            if drafting_status == "disabled"
            else "llm_not_configured_fallback"
        )
        updates["final_response_source"] = source
        log_node_event(
            state={**state, **updates},
            event_type=AuditEventType.LLM_RESPONSE_DRAFTING_SKIPPED,
            node_name="generate_customer_response",
            tool_name="draft_customer_response_with_llm",
            input_summary=llm_result.get("llm_input_payload"),
            output_summary={
                "drafting_status": drafting_status,
                "final_response_source": source,
            },
            reason=f"LLM response drafting {drafting_status}.",
        )
    elif drafting_status == "failed":
        updates["final_response_source"] = "llm_failed_fallback"
        log_node_event(
            state={**state, **updates},
            event_type=AuditEventType.LLM_RESPONSE_DRAFTING_FAILED,
            node_name="generate_customer_response",
            tool_name="draft_customer_response_with_llm",
            input_summary=llm_result.get("llm_input_payload"),
            output_summary={
                "drafting_status": "failed",
                "final_response_source": "llm_failed_fallback",
            },
            reason=llm_result.get("error_message"),
        )
    elif drafting_status == "completed":
        log_node_event(
            state={**state, **updates},
            event_type=AuditEventType.LLM_RESPONSE_DRAFTED,
            node_name="generate_customer_response",
            tool_name="draft_customer_response_with_llm",
            input_summary=llm_result.get("llm_input_payload"),
            output_summary={
                "drafting_status": "completed",
                "model_name": llm_result.get("model_name"),
                "usage": usage,
            },
            reason="LLM drafted customer response from minimized approved state.",
        )
        validation = validate_llm_customer_response(
            {**state, **updates},
            llm_result.get("llm_customer_response"),
        )
        updates.update(
            {
                "llm_validation_status": validation["validation_status"],
                "llm_validation_errors": validation["validation_errors"],
            }
        )
        if validation["validation_status"] == "passed":
            updates.update(
                {
                    "customer_response": llm_result.get("llm_customer_response")
                    or deterministic_response,
                    "final_response_source": "llm_validated",
                }
            )
            log_node_event(
                state={**state, **updates},
                event_type=AuditEventType.LLM_RESPONSE_VALIDATION_PASSED,
                node_name="generate_customer_response",
                input_summary={"drafting_status": "completed"},
                output_summary={
                    "validation_status": "passed",
                    "final_response_source": "llm_validated",
                },
                reason="LLM response passed deterministic safety validation.",
            )
        else:
            updates.update(
                {
                    "customer_response": deterministic_response,
                    "final_response_source": "llm_failed_fallback",
                }
            )
            log_node_event(
                state={**state, **updates},
                event_type=AuditEventType.LLM_RESPONSE_VALIDATION_FAILED,
                node_name="generate_customer_response",
                input_summary={"drafting_status": "completed"},
                output_summary={
                    "validation_status": "failed",
                    "validation_errors": validation["validation_errors"],
                    "final_response_source": "llm_failed_fallback",
                },
                reason="LLM response failed deterministic safety validation.",
            )

    log_node_event(
        state={**state, **updates},
        event_type=AuditEventType.CUSTOMER_RESPONSE_GENERATED,
        node_name="generate_customer_response",
        tool_name="generate_customer_response",
        input_summary={
            "eligibility_status": state.get("eligibility_status"),
            "replacement_request_id": state.get("replacement_request_id"),
            "escalation_id": state.get("escalation_id"),
        },
        output_summary={
            "response_type": result["response_type"],
            "final_response_source": updates.get("final_response_source"),
            "llm_drafting_status": updates.get("llm_drafting_status"),
            "llm_validation_status": updates.get("llm_validation_status"),
            "workflow_status": "completed",
        },
        reason=reason,
    )
    return updates
