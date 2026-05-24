from typing import Any

from app.audit.events import AuditEventType
from app.audit.store import clear_audit_events, get_audit_events
from app.tools.mock_data import PRIMARY_CUSTOMER_ID, PRIMARY_ORDER_ID
from app.workflow.graph import run_warranty_workflow
from app.workflow.state import WarrantyWorkflowState


def _base_state(
    workflow_id: str,
    customer_id: str = PRIMARY_CUSTOMER_ID,
    order_id: str = PRIMARY_ORDER_ID,
) -> WarrantyWorkflowState:
    return {
        "workflow_id": workflow_id,
        "correlation_id": f"corr_{workflow_id}",
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


def _event_types(workflow_id: str) -> list[str]:
    return [event.event_type for event in get_audit_events(workflow_id)]


def test_primary_cracked_screen_audit_timeline() -> None:
    clear_audit_events()
    workflow_id = "wf_audit_primary"

    run_warranty_workflow(_base_state(workflow_id))

    events = get_audit_events(workflow_id)
    event_types = _event_types(workflow_id)
    assert events
    assert AuditEventType.WORKFLOW_STARTED in event_types
    assert AuditEventType.IDENTITY_VERIFIED in event_types
    assert AuditEventType.ORDER_LOOKUP_COMPLETED in event_types
    assert AuditEventType.POLICY_RETRIEVED in event_types
    assert AuditEventType.ELIGIBILITY_CHECKED in event_types
    assert AuditEventType.GUARDRAIL_DECISION in event_types
    assert AuditEventType.CUSTOMER_RESPONSE_GENERATED in event_types
    assert AuditEventType.WORKFLOW_COMPLETED in event_types
    assert AuditEventType.REPLACEMENT_REQUEST_CREATED not in event_types

    policy_event = next(
        event for event in events if event.event_type == AuditEventType.POLICY_RETRIEVED
    )
    assert policy_event.policy_reference

    guardrail_event = next(
        event for event in events if event.event_type == AuditEventType.GUARDRAIL_DECISION
    )
    assert guardrail_event.guardrail_decision == "block"
    assert guardrail_event.output_summary["guardrail_decision"] == "block"


def test_eligible_replacement_audit_timeline(monkeypatch: Any) -> None:
    clear_audit_events()
    workflow_id = "wf_audit_eligible"

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

    run_warranty_workflow(_base_state(workflow_id))

    event_types = _event_types(workflow_id)
    assert AuditEventType.REPLACEMENT_REQUEST_CREATED in event_types
    assert AuditEventType.WORKFLOW_COMPLETED in event_types


def test_unknown_customer_audit_timeline_records_escalation() -> None:
    clear_audit_events()
    workflow_id = "wf_audit_unknown_customer"

    run_warranty_workflow(_base_state(workflow_id, customer_id="cust_unknown"))

    event_types = _event_types(workflow_id)
    assert AuditEventType.HUMAN_ESCALATION_CREATED in event_types
    assert AuditEventType.WORKFLOW_COMPLETED in event_types
