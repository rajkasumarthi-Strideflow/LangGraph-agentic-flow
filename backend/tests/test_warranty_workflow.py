from typing import Any

from app.audit.events import AuditEventType
from app.audit.store import clear_audit_events, get_audit_events
from app.tools.mock_data import PRIMARY_CUSTOMER_ID, PRIMARY_ORDER_ID
from app.tools.mock_data import ELIGIBLE_POWER_ORDER_ID
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
        "llm_drafting_status": None,
        "llm_customer_response": None,
        "llm_model_name": None,
        "llm_input_tokens": None,
        "llm_output_tokens": None,
        "llm_total_tokens": None,
        "llm_cached_tokens": None,
        "llm_validation_status": None,
        "llm_validation_errors": None,
        "final_response_source": None,
        "error_category": None,
        "workflow_status": "started",
    }


def test_primary_cracked_screen_workflow_blocks_replacement() -> None:
    clear_audit_events()
    result = run_warranty_workflow(_base_state())
    event_types = [event.event_type for event in get_audit_events("wf_test_001")]

    assert result["workflow_status"] == "completed"
    assert result["identity_verified"] is True
    assert result["order_retrieved"] is True
    assert result["policy_reference"] is not None
    assert result["eligibility_status"] == "not_eligible"
    assert result["guardrail_decision"] in {"block", None}
    assert result["replacement_request_id"] is None
    assert result["customer_response"]
    assert "replacement request has been created" not in result["customer_response"]
    assert result["llm_drafting_status"] == "not_configured"
    assert result["final_response_source"] == "llm_not_configured_fallback"
    assert AuditEventType.LLM_RESPONSE_DRAFTING_SKIPPED in event_types


def test_unknown_customer_workflow_routes_to_escalation() -> None:
    result = run_warranty_workflow(_base_state(customer_id="cust_unknown"))

    assert result["workflow_status"] == "completed"
    assert result["identity_verified"] is False
    assert result["escalation_required"] is True
    assert result["escalation_id"]
    assert "routed for human review" in result["customer_response"]


def test_eligible_power_failure_workflow_creates_replacement() -> None:
    clear_audit_events()
    state = _base_state(order_id=ELIGIBLE_POWER_ORDER_ID)
    state.update(
        {
            "workflow_id": "wf_eligible_power_001",
            "correlation_id": "corr_eligible_power_001",
            "customer_request": (
                "My laptop stopped powering on after 6 months. "
                "Can I get a replacement?"
            ),
        }
    )

    result = run_warranty_workflow(state)
    events = get_audit_events("wf_eligible_power_001")
    event_types = [event.event_type for event in events]
    guardrail_events = [
        event for event in events if event.event_type == AuditEventType.GUARDRAIL_DECISION
    ]

    assert result["workflow_status"] == "completed"
    assert result["identity_verified"] is True
    assert result["order_retrieved"] is True
    assert result["customer_authorized"] is True
    assert result["order_status"] == "delivered"
    assert result["purchase_age_months"] == 6
    assert result["eligibility_status"] == "eligible"
    assert result["inventory_available"] is True
    assert result["guardrail_decision"] == "allow"
    assert result["replacement_request_id"] == f"repl_{ELIGIBLE_POWER_ORDER_ID}"
    assert result["replacement_status"] == "created"
    assert "replacement request has been created" in result["customer_response"]
    assert "shipment is on the way" not in result["customer_response"].lower()
    assert "has been shipped" not in result["customer_response"].lower()
    assert AuditEventType.ELIGIBILITY_CHECKED in event_types
    assert AuditEventType.INVENTORY_CHECKED in event_types
    assert AuditEventType.GUARDRAIL_DECISION in event_types
    assert AuditEventType.REPLACEMENT_REQUEST_CREATED in event_types
    assert AuditEventType.WORKFLOW_COMPLETED in event_types
    assert guardrail_events[-1].guardrail_decision == "allow"


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


def test_valid_llm_draft_replaces_deterministic_response(monkeypatch: Any) -> None:
    def fake_draft_customer_response_with_llm(state: dict) -> dict[str, Any]:
        return {
            "drafting_status": "completed",
            "llm_customer_response": "Based on the current policy, this item is not automatically eligible for replacement because cracked screens from accidental damage are excluded.",
            "model_name": "test-model",
            "llm_input_payload": {"eligibility_status": state.get("eligibility_status")},
            "usage": {
                "input_tokens": 10,
                "output_tokens": 12,
                "total_tokens": 22,
                "cached_tokens": 0,
            },
            "error_message": None,
        }

    monkeypatch.setattr(
        "app.workflow.nodes.draft_customer_response_with_llm",
        fake_draft_customer_response_with_llm,
    )

    result = run_warranty_workflow(_base_state())

    assert result["customer_response"].startswith("Based on the current policy")
    assert result["final_response_source"] == "llm_validated"
    assert result["llm_validation_status"] == "passed"
    assert result["llm_model_name"] == "test-model"
    assert result["llm_total_tokens"] == 22


def test_unsafe_llm_draft_falls_back_to_deterministic_response(
    monkeypatch: Any,
) -> None:
    def fake_draft_customer_response_with_llm(state: dict) -> dict[str, Any]:
        return {
            "drafting_status": "completed",
            "llm_customer_response": "Your replacement request has been created and you are eligible for shipment.",
            "model_name": "test-model",
            "llm_input_payload": {"eligibility_status": state.get("eligibility_status")},
            "usage": {
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
                "cached_tokens": None,
            },
            "error_message": None,
        }

    monkeypatch.setattr(
        "app.workflow.nodes.draft_customer_response_with_llm",
        fake_draft_customer_response_with_llm,
    )

    result = run_warranty_workflow(_base_state())

    assert result["final_response_source"] == "llm_failed_fallback"
    assert result["llm_validation_status"] == "failed"
    assert result["llm_validation_errors"]
    assert "replacement request has been created" not in result["customer_response"]
