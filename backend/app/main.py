from typing import Any
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.audit.store import get_audit_events
from app.models.api import (
    AuditTimelineResponse,
    HumanReviewRequest,
    HumanReviewResponse,
    StartWorkflowRequest,
    StartWorkflowResponse,
    WorkflowStateResponse,
)
from app.workflow.graph import run_warranty_workflow
from app.workflow.state import WarrantyWorkflowState
from app.workflow.store import get_workflow_result, save_workflow_result

app = FastAPI(
    title="WarrantyWise Agentic Support Platform",
    version="0.1.0",
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


def _build_initial_state(
    workflow_id: str,
    correlation_id: str,
    request: StartWorkflowRequest,
) -> WarrantyWorkflowState:
    return {
        "workflow_id": workflow_id,
        "correlation_id": correlation_id,
        "customer_request": request.customer_request,
        "customer_id": request.customer_id,
        "order_id": request.order_id,
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


def _workflow_response(state: dict[str, Any]) -> StartWorkflowResponse:
    return StartWorkflowResponse(
        workflow_id=state["workflow_id"],
        correlation_id=state["correlation_id"],
        workflow_status=state["workflow_status"],
        eligibility_status=state.get("eligibility_status"),
        guardrail_decision=state.get("guardrail_decision"),
        replacement_request_id=state.get("replacement_request_id"),
        escalation_id=state.get("escalation_id"),
        customer_response=state.get("customer_response"),
    )


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "warrantywise-agentic-support",
        "version": "0.1.0",
    }


@app.get("/", response_class=FileResponse)
def frontend_index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/api/workflows/start", response_model=StartWorkflowResponse)
def start_workflow(request: StartWorkflowRequest) -> StartWorkflowResponse:
    workflow_id = f"wf_{uuid4().hex}"
    correlation_id = f"corr_{uuid4().hex}"
    initial_state = _build_initial_state(workflow_id, correlation_id, request)
    final_state = run_warranty_workflow(initial_state)
    saved_state = save_workflow_result(workflow_id, dict(final_state))
    return _workflow_response(saved_state)


@app.get("/api/workflows/{workflow_id}", response_model=WorkflowStateResponse)
def get_workflow_state(workflow_id: str) -> WorkflowStateResponse:
    state = get_workflow_result(workflow_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Workflow not found.")

    return WorkflowStateResponse(workflow_id=workflow_id, state=state)


@app.get("/api/workflows/{workflow_id}/audit", response_model=AuditTimelineResponse)
def get_workflow_audit(workflow_id: str) -> AuditTimelineResponse:
    state = get_workflow_result(workflow_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Workflow not found.")

    events = [
        event.model_dump(mode="json") for event in get_audit_events(workflow_id)
    ]
    return AuditTimelineResponse(workflow_id=workflow_id, events=events)


@app.post(
    "/api/workflows/{workflow_id}/human-review",
    response_model=HumanReviewResponse,
)
def submit_human_review(
    workflow_id: str,
    request: HumanReviewRequest,
) -> HumanReviewResponse:
    state = get_workflow_result(workflow_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Workflow not found.")

    if not state.get("escalation_id"):
        return HumanReviewResponse(
            workflow_id=workflow_id,
            decision=request.decision,
            reviewer_id=request.reviewer_id,
            status="not_required",
            message="No human review is currently required for this workflow.",
        )

    state.update(
        {
            "human_review_decision": request.decision,
            "human_reviewer_id": request.reviewer_id,
            "human_review_reason": request.reason,
            "human_review_status": "completed",
        }
    )
    save_workflow_result(workflow_id, state)

    return HumanReviewResponse(
        workflow_id=workflow_id,
        decision=request.decision,
        reviewer_id=request.reviewer_id,
        status="completed",
        message="Human review simulation completed.",
    )
