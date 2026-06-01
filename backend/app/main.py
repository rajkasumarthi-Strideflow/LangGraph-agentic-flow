from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.audit.human_review_store import get_human_reviews, save_human_review
from app.audit.store import get_audit_events, get_audit_events_by_correlation_id
from app.correlation import generate_correlation_id
from app.database import init_db
from app.intake.router import route_customer_message
from app.intake.session import (
    IntakeSession,
    create_intake_session,
    get_intake_session_by_correlation_id,
    get_intake_session,
    update_intake_session,
)
from app.models.api import (
    AuditTimelineResponse,
    HumanReviewRequest,
    HumanReviewResponse,
    IntakeRouteRequest,
    IntakeRouteResponse,
    IntakeSessionReplyRequest,
    IntakeSessionResponse,
    IntakeSessionStartRequest,
    MonitoringOutcomesResponse,
    MonitoringRunsResponse,
    MonitoringSummaryResponse,
    StartWorkflowRequest,
    StartWorkflowResponse,
    WorkflowStateResponse,
)
from app.monitoring.service import (
    WORKFLOW_TYPES,
    build_workflow_monitoring_summary,
    list_monitoring_outcome_filters,
    list_recent_workflow_runs,
)
from app.observability.langsmith_tracing import get_langsmith_status
from app.workflow.graph import run_warranty_workflow
from app.workflow.state import WarrantyWorkflowState
from app.workflow.store import (
    get_workflow_result,
    get_workflow_result_by_correlation_id,
    save_workflow_result,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(
    title="WarrantyWise Agentic Support Platform",
    version="0.1.0",
    lifespan=lifespan,
)

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
        llm_drafting_status=state.get("llm_drafting_status"),
        llm_model_name=state.get("llm_model_name"),
        llm_validation_status=state.get("llm_validation_status"),
        final_response_source=state.get("final_response_source"),
    )


def _intake_session_response(session: IntakeSession) -> IntakeSessionResponse:
    data = session.model_dump(mode="json")
    return IntakeSessionResponse(**data)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "warrantywise-agentic-support",
        "version": "0.1.0",
    }


@app.get("/api/observability/status")
def get_observability_status() -> dict[str, Any]:
    return get_langsmith_status()


@app.get("/", response_class=FileResponse)
def frontend_index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/api/intake/route", response_model=IntakeRouteResponse)
def route_intake_request(request: IntakeRouteRequest) -> IntakeRouteResponse:
    result = route_customer_message(
        message=request.message,
        customer_id=request.customer_id,
        order_id=request.order_id,
    )
    result["can_start_workflow"] = bool(result.get("can_start_workflow")) and (
        result.get("routed_workflow") == "warranty_replacement"
        and not result.get("requires_clarification")
    )
    return IntakeRouteResponse(**result)


@app.post(
    "/api/intake/session/start",
    response_model=IntakeSessionResponse,
)
def start_intake_session(
    request: IntakeSessionStartRequest,
) -> IntakeSessionResponse:
    session = create_intake_session(
        request.message,
        correlation_id=generate_correlation_id(),
    )
    return _intake_session_response(session)


@app.post(
    "/api/intake/session/{intake_session_id}/reply",
    response_model=IntakeSessionResponse,
)
def reply_to_intake_session(
    intake_session_id: str,
    request: IntakeSessionReplyRequest,
) -> IntakeSessionResponse:
    session = update_intake_session(intake_session_id, request.message)
    if session is None:
        raise HTTPException(status_code=404, detail="Intake session not found.")

    return _intake_session_response(session)


@app.get(
    "/api/intake/session/{intake_session_id}",
    response_model=IntakeSessionResponse,
)
def get_intake_session_state(
    intake_session_id: str,
) -> IntakeSessionResponse:
    session = get_intake_session(intake_session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Intake session not found.")

    return _intake_session_response(session)


@app.post("/api/workflows/start", response_model=StartWorkflowResponse)
def start_workflow(request: StartWorkflowRequest) -> StartWorkflowResponse:
    workflow_id = f"wf_{uuid4().hex}"
    correlation_id = request.correlation_id or generate_correlation_id()
    initial_state = _build_initial_state(workflow_id, correlation_id, request)
    final_state = run_warranty_workflow(initial_state)
    saved_state = save_workflow_result(workflow_id, dict(final_state))
    return _workflow_response(saved_state)


@app.get("/api/workflows/{workflow_id}", response_model=WorkflowStateResponse)
def get_workflow_state(workflow_id: str) -> WorkflowStateResponse:
    state = get_workflow_result(workflow_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Workflow not found.")

    return WorkflowStateResponse(
        workflow_id=workflow_id,
        correlation_id=state.get("correlation_id"),
        state=state,
    )


@app.get("/api/workflows/{workflow_id}/audit", response_model=AuditTimelineResponse)
def get_workflow_audit(workflow_id: str) -> AuditTimelineResponse:
    state = get_workflow_result(workflow_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Workflow not found.")

    events = [
        event.model_dump(mode="json") for event in get_audit_events(workflow_id)
    ]
    return AuditTimelineResponse(
        workflow_id=workflow_id,
        correlation_id=state.get("correlation_id"),
        events=events,
    )


@app.get("/api/correlation/{correlation_id}")
def get_correlation_view(correlation_id: str) -> dict[str, Any]:
    intake_session = get_intake_session_by_correlation_id(correlation_id)
    workflow_state = get_workflow_result_by_correlation_id(correlation_id)
    audit_events = get_audit_events_by_correlation_id(correlation_id)

    if intake_session is None and workflow_state is None and not audit_events:
        raise HTTPException(status_code=404, detail="Correlation ID not found.")

    return {
        "correlation_id": correlation_id,
        "intake_session_id": (
            intake_session.intake_session_id if intake_session is not None else None
        ),
        "workflow_id": workflow_state.get("workflow_id") if workflow_state else None,
        "audit_event_count": len(audit_events),
        "workflow_status": (
            workflow_state.get("workflow_status") if workflow_state else None
        ),
        "final_response_source": (
            workflow_state.get("final_response_source") if workflow_state else None
        ),
    }


@app.get("/api/monitoring/summary", response_model=MonitoringSummaryResponse)
def get_monitoring_summary(
    workflow_type: str | None = None,
    outcome: str | None = None,
) -> MonitoringSummaryResponse:
    return MonitoringSummaryResponse(
        **build_workflow_monitoring_summary(
            workflow_type=workflow_type,
            outcome=outcome,
        )
    )


@app.get("/api/monitoring/runs", response_model=MonitoringRunsResponse)
def get_monitoring_runs(
    workflow_type: str | None = None,
    outcome: str | None = None,
    correlation_id: str | None = None,
    limit: int = 25,
) -> MonitoringRunsResponse:
    return MonitoringRunsResponse(
        runs=list_recent_workflow_runs(
            workflow_type=workflow_type,
            outcome=outcome,
            correlation_id=correlation_id,
            limit=limit,
        )
    )


@app.get("/api/monitoring/outcomes", response_model=MonitoringOutcomesResponse)
def get_monitoring_outcomes() -> MonitoringOutcomesResponse:
    return MonitoringOutcomesResponse(
        workflow_types=WORKFLOW_TYPES,
        outcomes=list_monitoring_outcome_filters(),
    )


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

    save_human_review(
        workflow_id=workflow_id,
        escalation_id=state.get("escalation_id"),
        reviewer_id=request.reviewer_id,
        decision=request.decision,
        reason=request.reason,
        status="completed",
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


@app.get("/api/workflows/{workflow_id}/human-reviews")
def get_workflow_human_reviews(workflow_id: str) -> dict[str, Any]:
    state = get_workflow_result(workflow_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Workflow not found.")

    return {
        "workflow_id": workflow_id,
        "reviews": get_human_reviews(workflow_id),
    }
