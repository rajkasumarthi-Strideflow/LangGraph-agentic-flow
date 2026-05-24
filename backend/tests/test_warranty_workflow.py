from typing import Any

from app.tools.mock_data import PRIMARY_CUSTOMER_ID, PRIMARY_ORDER_ID
from app.workflow.graph import run_warranty_workflow
from app.workflow.nodes import create_replacement_request_node
from app.workflow.state import WarrantyWorkflowState


def _base_state(
    customer_id: str = PRIMARY_CUSTOMER_ID,
    order_id: str = PRIMARY_ORDER_ID,
) -> WarrantyWorkflowState:
    return {
        "workflow_id": "wf_test_001",
        "correlation_id": "corr_test_001",
        "customer_request": "My laptop screen cracked after 9 months. Can I get a replacement?",
        "customer_id": customer_id,
        "order_id": order_id,
        "product_id": None,
        "product_family": None,
        "identity_verified": False,
        "customer_authorized": False,
        "order_retrieved": False,
        "order_status": None,
        "purchase_age_months": None,
        "policy_id": None,
        "policy_reference": None,
        "policy_version": None,
        "eligibility_status": None,
        "eligibility_reason": None,
        "inventory_available": None,
        "inventory_status": None,
        "replacement_request_id": None,
        "replacement_status": None,
        "escalation_id": None,
        "escalation_required": False,
        "escalation_reason": None,
        "guardrail_decision": None,
        "customer_response": None,
        "response_type": None,
        "error_category": None,
        "workflow_status": "started",
    }


def test_primary_cracked_screen_workflow_blocks_replacement() -> None:
    result = run_warranty_workflow(_base_state())

    assert result["workflow_status"] == "completed"
    assert result["identity_verified"] is True
    assert result["order_retrieved"] is True
    assert result["policy_reference"] is not None
    assert result["eligibility_status"] == "not_eligible"
    assert result["guardrail_decision"] in {"block", None}
    assert result["replacement_request_id"] is None
    assert result["customer_response"]
    assert "replacement request has been created" not in result["customer_response"]


def test_unknown_customer_workflow_routes_to_escalation() -> None:
    result = run_warranty_workflow(_base_state(customer_id="cust_unknown"))

    assert result["workflow_status"] == "completed"
    assert result["identity_verified"] is False
    assert result["escalation_required"] is True
    assert result["escalation_id"]
    assert "routed for human review" in result["customer_response"]


def test_eligible_replacement_workflow_creates_replacement(
    monkeypatch: Any,
) -> None:
    def eligible_check_replacement_eligibility(
        customer_id: str,
        order_id: str,
        policy_id: str,
    ) -> dict[str, Any]:
        return {
            "result_status": "success",
            "customer_id": customer_id,
            "order_id": order_id,
            "product_id": "prod_laptop_001",
            "eligibility_status": "eligible",
            "policy_reference": f"{policy_id}#v2.0",
            "policy_version": "2.0",
            "reason": "Manufacturing defect is covered by the current warranty policy.",
        }

    monkeypatch.setattr(
        "app.workflow.nodes.check_replacement_eligibility",
        eligible_check_replacement_eligibility,
    )

    result = run_warranty_workflow(_base_state())

    assert result["workflow_status"] == "completed"
    assert result["guardrail_decision"] == "allow"
    assert result["replacement_request_id"]
    assert result["replacement_status"] == "created"
    assert "replacement request has been created" in result["customer_response"]


def test_create_replacement_request_node_does_not_create_when_not_eligible() -> None:
    state = _base_state()
    state.update(
        {
            "product_id": "prod_laptop_001",
            "eligibility_status": "not_eligible",
            "inventory_available": True,
            "guardrail_decision": "block",
        }
    )

    result = create_replacement_request_node(state)

    assert result["replacement_request_id"] is None
    assert result["replacement_status"] == "not_created"
