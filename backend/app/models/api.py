from typing import Any

from pydantic import BaseModel


class StartWorkflowRequest(BaseModel):
    customer_request: str
    customer_id: str
    order_id: str


class IntakeRouteRequest(BaseModel):
    message: str
    customer_id: str | None = None
    order_id: str | None = None


class IntakeRouteResponse(BaseModel):
    intent: str
    confidence: float | None = None
    product_type: str | None = None
    product_issue: str | None = None
    damage_type: str | None = None
    customer_id: str | None = None
    order_id: str | None = None
    requires_order_lookup: bool
    requires_policy_lookup: bool
    requires_clarification: bool
    missing_fields: list[str]
    next_question: str | None = None
    routed_workflow: str | None = None
    routing_status: str
    error_message: str | None = None
    can_start_workflow: bool = False


class StartWorkflowResponse(BaseModel):
    workflow_id: str
    correlation_id: str
    workflow_status: str
    eligibility_status: str | None
    guardrail_decision: str | None
    replacement_request_id: str | None
    escalation_id: str | None
    customer_response: str | None
    llm_drafting_status: str | None = None
    llm_model_name: str | None = None
    llm_validation_status: str | None = None
    final_response_source: str | None = None


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
