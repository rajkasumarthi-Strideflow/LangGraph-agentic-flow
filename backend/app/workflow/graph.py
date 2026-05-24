from typing import Any

from langgraph.graph import END, START, StateGraph

from app.audit.logger import (
    log_workflow_completed,
    log_workflow_failed,
    log_workflow_started,
)
from app.workflow.nodes import (
    check_inventory_availability_node,
    check_replacement_eligibility_node,
    create_replacement_request_node,
    escalate_to_human_node,
    generate_customer_response_node,
    guardrail_check_node,
    lookup_order_node,
    retrieve_warranty_policy_node,
    verify_identity_node,
)
from app.workflow.state import WarrantyWorkflowState


def route_after_identity(state: WarrantyWorkflowState) -> str:
    if state.get("identity_verified") is False:
        return "escalate_to_human"
    return "lookup_order"


def route_after_order(state: WarrantyWorkflowState) -> str:
    if state.get("order_retrieved") is False or state.get("customer_authorized") is False:
        return "escalate_to_human"
    return "retrieve_warranty_policy"


def route_after_policy(state: WarrantyWorkflowState) -> str:
    if not state.get("policy_reference"):
        return "escalate_to_human"
    return "check_replacement_eligibility"


def route_after_eligibility(state: WarrantyWorkflowState) -> str:
    if state.get("eligibility_status") == "not_eligible":
        return "guardrail_check"
    if state.get("eligibility_status") in {"unknown", "human_review_required"}:
        return "escalate_to_human"
    return "check_inventory_availability"


def route_after_guardrail(state: WarrantyWorkflowState) -> str:
    if state.get("guardrail_decision") == "allow":
        return "create_replacement_request"
    if state.get("guardrail_decision") == "block":
        return "generate_customer_response"
    return "escalate_to_human"


def build_warranty_workflow() -> Any:
    graph = StateGraph(WarrantyWorkflowState)

    graph.add_node("verify_identity", verify_identity_node)
    graph.add_node("lookup_order", lookup_order_node)
    graph.add_node("retrieve_warranty_policy", retrieve_warranty_policy_node)
    graph.add_node(
        "check_replacement_eligibility",
        check_replacement_eligibility_node,
    )
    graph.add_node("check_inventory_availability", check_inventory_availability_node)
    graph.add_node("guardrail_check", guardrail_check_node)
    graph.add_node("create_replacement_request", create_replacement_request_node)
    graph.add_node("escalate_to_human", escalate_to_human_node)
    graph.add_node("generate_customer_response", generate_customer_response_node)

    graph.add_edge(START, "verify_identity")
    graph.add_conditional_edges("verify_identity", route_after_identity)
    graph.add_conditional_edges("lookup_order", route_after_order)
    graph.add_conditional_edges("retrieve_warranty_policy", route_after_policy)
    graph.add_conditional_edges(
        "check_replacement_eligibility",
        route_after_eligibility,
    )
    graph.add_edge("check_inventory_availability", "guardrail_check")
    graph.add_conditional_edges("guardrail_check", route_after_guardrail)
    graph.add_edge("create_replacement_request", "generate_customer_response")
    graph.add_edge("escalate_to_human", "generate_customer_response")
    graph.add_edge("generate_customer_response", END)

    return graph.compile()


def run_warranty_workflow(
    initial_state: WarrantyWorkflowState,
) -> WarrantyWorkflowState:
    workflow = build_warranty_workflow()
    log_workflow_started(initial_state)
    try:
        final_state = workflow.invoke(initial_state)
    except Exception as exc:
        log_workflow_failed(initial_state, reason=str(exc))
        raise

    log_workflow_completed(final_state)
    return final_state
