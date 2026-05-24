from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AuditEventType(StrEnum):
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
