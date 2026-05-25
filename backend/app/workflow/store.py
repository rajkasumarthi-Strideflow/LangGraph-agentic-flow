from typing import Any

from app.database import SessionLocal, init_db
from app.models.db import WorkflowRunORM


def save_workflow_result(workflow_id: str, state: dict[str, Any]) -> dict[str, Any]:
    init_db()
    with SessionLocal() as db:
        workflow = (
            db.query(WorkflowRunORM)
            .filter(WorkflowRunORM.workflow_id == workflow_id)
            .one_or_none()
        )
        if workflow is None:
            workflow = WorkflowRunORM(
                workflow_id=workflow_id,
                correlation_id=state["correlation_id"],
                workflow_status=state["workflow_status"],
                customer_id=state["customer_id"],
                order_id=state["order_id"],
                final_state=state,
            )
            db.add(workflow)
        else:
            workflow.correlation_id = state["correlation_id"]
            workflow.workflow_status = state["workflow_status"]
            workflow.customer_id = state["customer_id"]
            workflow.order_id = state["order_id"]
            workflow.final_state = state
        db.commit()
    return state


def get_workflow_result(workflow_id: str) -> dict[str, Any] | None:
    init_db()
    with SessionLocal() as db:
        workflow = (
            db.query(WorkflowRunORM)
            .filter(WorkflowRunORM.workflow_id == workflow_id)
            .one_or_none()
        )
        if workflow is None:
            return None
        return dict(workflow.final_state)


def clear_workflow_results() -> None:
    init_db()
    with SessionLocal() as db:
        db.query(WorkflowRunORM).delete()
        db.commit()
