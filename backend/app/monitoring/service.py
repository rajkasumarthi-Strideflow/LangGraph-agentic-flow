from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from app.audit.store import get_audit_events
from app.database import SessionLocal, init_db
from app.models.db import WorkflowRunORM

VISIBLE_WORKFLOW_OUTCOMES = [
    "blocked",
    "escalated",
    "allowed_action",
    "completed_no_action",
    "failed",
]
INTERNAL_OUTCOMES = [
    "clarification_required",
    "invalid_input",
    "unknown",
]
WORKFLOW_TYPES = ["warranty_replacement"]


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _workflow_type(final_state: dict[str, Any]) -> str:
    return str(final_state.get("workflow_type") or "warranty_replacement")


def derive_workflow_outcome(
    final_state: dict[str, Any],
    audit_events: list[Any] | None = None,
) -> str:
    workflow_status = final_state.get("workflow_status")
    if workflow_status == "failed":
        return "failed"
    if final_state.get("escalation_id"):
        return "escalated"
    if final_state.get("replacement_request_id"):
        return "allowed_action"
    if final_state.get("guardrail_decision") == "block":
        return "blocked"
    if final_state.get("eligibility_status") == "not_eligible":
        return "blocked"
    if workflow_status == "completed":
        return "completed_no_action"
    return "unknown"


def count_tool_calls(audit_events: list[Any]) -> int:
    return sum(1 for event in audit_events if getattr(event, "tool_name", None))


def count_audit_events(audit_events: list[Any]) -> int:
    return len(audit_events)


def _run_row(workflow: WorkflowRunORM) -> dict[str, Any]:
    final_state = dict(workflow.final_state or {})
    audit_events = get_audit_events(workflow.workflow_id)
    outcome = derive_workflow_outcome(final_state, audit_events)
    return {
        "workflow_id": workflow.workflow_id,
        "correlation_id": workflow.correlation_id,
        "workflow_type": _workflow_type(final_state),
        "workflow_status": final_state.get("workflow_status")
        or workflow.workflow_status,
        "outcome": outcome,
        "eligibility_status": final_state.get("eligibility_status"),
        "guardrail_decision": final_state.get("guardrail_decision"),
        "escalation_id": final_state.get("escalation_id"),
        "replacement_request_id": final_state.get("replacement_request_id"),
        "llm_drafting_status": final_state.get("llm_drafting_status"),
        "llm_validation_status": final_state.get("llm_validation_status"),
        "final_response_source": final_state.get("final_response_source"),
        "llm_input_tokens": final_state.get("llm_input_tokens"),
        "llm_output_tokens": final_state.get("llm_output_tokens"),
        "llm_total_tokens": final_state.get("llm_total_tokens"),
        "audit_event_count": count_audit_events(audit_events),
        "tool_call_count": count_tool_calls(audit_events),
        "created_at": _iso(workflow.created_at),
        "updated_at": _iso(workflow.updated_at),
    }


def list_recent_workflow_runs(
    *,
    workflow_type: str | None = None,
    outcome: str | None = None,
    correlation_id: str | None = None,
    limit: int = 25,
) -> list[dict[str, Any]]:
    init_db()
    safe_limit = min(max(limit, 1), 100)
    with SessionLocal() as db:
        query = db.query(WorkflowRunORM)
        if correlation_id:
            query = query.filter(WorkflowRunORM.correlation_id == correlation_id)
        rows = (
            query.order_by(WorkflowRunORM.updated_at.desc(), WorkflowRunORM.id.desc())
            .limit(250)
            .all()
        )

    run_rows = [_run_row(workflow) for workflow in rows]
    if workflow_type:
        run_rows = [row for row in run_rows if row["workflow_type"] == workflow_type]
    if outcome:
        run_rows = [row for row in run_rows if row["outcome"] == outcome]
    return run_rows[:safe_limit]


def build_workflow_monitoring_summary(
    *,
    workflow_type: str | None = None,
    outcome: str | None = None,
) -> dict[str, Any]:
    runs = list_recent_workflow_runs(
        workflow_type=workflow_type,
        outcome=outcome,
        limit=100,
    )
    workflow_type_counts = Counter(row["workflow_type"] for row in runs)
    outcome_counts = Counter(row["outcome"] for row in runs)

    visible_outcomes = [*VISIBLE_WORKFLOW_OUTCOMES]
    if outcome_counts.get("unknown", 0) > 0:
        visible_outcomes.append("unknown")

    return {
        "total_workflow_runs": len(runs),
        "completed_runs": sum(
            1 for row in runs if row.get("workflow_status") == "completed"
        ),
        "failed_runs": sum(1 for row in runs if row["outcome"] == "failed"),
        "blocked_count": sum(1 for row in runs if row["outcome"] == "blocked"),
        "escalated_count": sum(1 for row in runs if row["outcome"] == "escalated"),
        "allowed_action_count": sum(
            1 for row in runs if row["outcome"] == "allowed_action"
        ),
        "replacement_request_count": sum(
            1 for row in runs if row.get("replacement_request_id")
        ),
        "llm_drafting_completed_count": sum(
            1 for row in runs if row.get("llm_drafting_status") == "completed"
        ),
        "llm_validation_failed_count": sum(
            1 for row in runs if row.get("llm_validation_status") == "failed"
        ),
        "total_input_tokens": sum(row.get("llm_input_tokens") or 0 for row in runs),
        "total_output_tokens": sum(row.get("llm_output_tokens") or 0 for row in runs),
        "total_tokens": sum(row.get("llm_total_tokens") or 0 for row in runs),
        "total_audit_events": sum(row["audit_event_count"] for row in runs),
        "total_tool_calls": sum(row["tool_call_count"] for row in runs),
        "workflow_type_breakdown": dict(workflow_type_counts),
        "outcome_breakdown": {
            allowed: outcome_counts.get(allowed, 0)
            for allowed in visible_outcomes
        },
    }


def list_monitoring_outcome_filters() -> list[str]:
    outcomes = [*VISIBLE_WORKFLOW_OUTCOMES]
    runs = list_recent_workflow_runs(limit=100)
    if any(row["outcome"] == "unknown" for row in runs):
        outcomes.append("unknown")
    return outcomes
