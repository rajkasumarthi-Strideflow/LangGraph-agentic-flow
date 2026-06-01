from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.audit.events import AuditEvent, AuditEventType
from app.audit.store import record_audit_event
from app.workflow.state import WarrantyWorkflowState


def create_audit_event(
    workflow_id: str,
    correlation_id: str,
    event_type: str,
    actor: str = "system",
    node_name: str | None = None,
    tool_name: str | None = None,
    input_summary: dict[str, Any] | None = None,
    output_summary: dict[str, Any] | None = None,
    policy_reference: str | None = None,
    guardrail_decision: str | None = None,
    reason: str | None = None,
) -> AuditEvent:
    if not correlation_id:
        raise ValueError("correlation_id is required for audit events.")

    safe_input_summary = {
        "correlation_id": correlation_id,
        **(input_summary or {}),
    }
    safe_output_summary = {
        "correlation_id": correlation_id,
        **(output_summary or {}),
    }

    event = AuditEvent(
        event_id=f"audit_{uuid4().hex}",
        workflow_id=workflow_id,
        correlation_id=correlation_id,
        event_type=event_type,
        timestamp=datetime.now(UTC),
        actor=actor,
        node_name=node_name,
        tool_name=tool_name,
        input_summary=safe_input_summary,
        output_summary=safe_output_summary,
        policy_reference=policy_reference,
        guardrail_decision=guardrail_decision,
        reason=reason,
    )
    return record_audit_event(event)


def log_workflow_started(state: WarrantyWorkflowState) -> AuditEvent:
    return create_audit_event(
        workflow_id=state["workflow_id"],
        correlation_id=state["correlation_id"],
        event_type=AuditEventType.WORKFLOW_STARTED,
        input_summary={
            "customer_id": state["customer_id"],
            "order_id": state["order_id"],
        },
        output_summary={"workflow_status": state["workflow_status"]},
        reason="Workflow run started.",
    )


def log_node_event(
    state: WarrantyWorkflowState,
    event_type: str,
    node_name: str,
    tool_name: str | None = None,
    input_summary: dict[str, Any] | None = None,
    output_summary: dict[str, Any] | None = None,
    reason: str | None = None,
) -> AuditEvent:
    summary = output_summary or {}
    return create_audit_event(
        workflow_id=state["workflow_id"],
        correlation_id=state["correlation_id"],
        event_type=event_type,
        node_name=node_name,
        tool_name=tool_name,
        input_summary=input_summary,
        output_summary=summary,
        policy_reference=summary.get("policy_reference") or state.get("policy_reference"),
        guardrail_decision=summary.get("guardrail_decision")
        or state.get("guardrail_decision"),
        reason=reason,
    )


def log_workflow_completed(state: WarrantyWorkflowState) -> AuditEvent:
    return create_audit_event(
        workflow_id=state["workflow_id"],
        correlation_id=state["correlation_id"],
        event_type=AuditEventType.WORKFLOW_COMPLETED,
        input_summary={
            "customer_id": state["customer_id"],
            "order_id": state["order_id"],
        },
        output_summary={
            "workflow_status": state["workflow_status"],
            "response_type": state.get("response_type"),
            "final_response_source": state.get("final_response_source"),
            "replacement_request_id": state.get("replacement_request_id"),
            "escalation_id": state.get("escalation_id"),
        },
        policy_reference=state.get("policy_reference"),
        guardrail_decision=state.get("guardrail_decision"),
        reason="Workflow run completed.",
    )


def log_workflow_failed(
    state: WarrantyWorkflowState,
    reason: str,
) -> AuditEvent:
    return create_audit_event(
        workflow_id=state["workflow_id"],
        correlation_id=state["correlation_id"],
        event_type=AuditEventType.WORKFLOW_FAILED,
        input_summary={
            "customer_id": state["customer_id"],
            "order_id": state["order_id"],
        },
        output_summary={
            "workflow_status": "failed",
            "error_category": state.get("error_category"),
        },
        policy_reference=state.get("policy_reference"),
        guardrail_decision=state.get("guardrail_decision"),
        reason=reason,
    )
