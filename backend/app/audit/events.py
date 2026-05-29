from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AuditEventType(StrEnum):
    INTAKE_ROUTER_STARTED = "intake_router_started"
    INTAKE_ROUTER_COMPLETED = "intake_router_completed"
    INTAKE_ROUTER_FAILED = "intake_router_failed"
    INTAKE_CLARIFICATION_REQUIRED = "intake_clarification_required"
    INTAKE_SESSION_STARTED = "intake_session_started"
    INTAKE_CLARIFICATION_REQUESTED = "intake_clarification_requested"
    INTAKE_SESSION_UPDATED = "intake_session_updated"
    INTAKE_READY_TO_ROUTE = "intake_ready_to_route"
    WORKFLOW_STARTED = "workflow_started"
    IDENTITY_VERIFIED = "identity_verified"
    ORDER_LOOKUP_COMPLETED = "order_lookup_completed"
    POLICY_RETRIEVED = "policy_retrieved"
    ELIGIBILITY_CHECKED = "eligibility_checked"
    INVENTORY_CHECKED = "inventory_checked"
    GUARDRAIL_DECISION = "guardrail_decision"
    REPLACEMENT_REQUEST_CREATED = "replacement_request_created"
    HUMAN_ESCALATION_CREATED = "human_escalation_created"
    CUSTOMER_RESPONSE_GENERATED = "customer_response_generated"
    LLM_RESPONSE_DRAFTING_SKIPPED = "llm_response_drafting_skipped"
    LLM_RESPONSE_DRAFTED = "llm_response_drafted"
    LLM_RESPONSE_VALIDATION_PASSED = "llm_response_validation_passed"
    LLM_RESPONSE_VALIDATION_FAILED = "llm_response_validation_failed"
    LLM_RESPONSE_DRAFTING_FAILED = "llm_response_drafting_failed"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"


class AuditEvent(BaseModel):
    event_id: str
    workflow_id: str
    correlation_id: str
    event_type: str
    timestamp: datetime
    actor: str = "system"
    node_name: str | None = None
    tool_name: str | None = None
    input_summary: dict[str, Any] = Field(default_factory=dict)
    output_summary: dict[str, Any] = Field(default_factory=dict)
    policy_reference: str | None = None
    guardrail_decision: str | None = None
    reason: str | None = None
