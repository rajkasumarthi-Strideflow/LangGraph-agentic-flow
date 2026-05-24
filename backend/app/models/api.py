from typing import Any

from pydantic import BaseModel


class StartWorkflowRequest(BaseModel):
    customer_request: str
    customer_id: str
    order_id: str


class StartWorkflowResponse(BaseModel):
    workflow_id: str
    correlation_id: str
    workflow_status: str
    eligibility_status: str | None
    guardrail_decision: str | None
    replacement_request_id: str | None
    escalation_id: str | None
    customer_response: str | None


class WorkflowStateResponse(BaseModel):
    workflow_id: str
    state: dict[str, Any]


class AuditTimelineResponse(BaseModel):
    workflow_id: str
    events: list[dict[str, Any]]


class HumanReviewRequest(BaseModel):
    decision: str
    reviewer_id: str
    reason: str | None = None


class HumanReviewResponse(BaseModel):
    workflow_id: str
    decision: str
    reviewer_id: str
    status: str
    message: str
