from datetime import datetime, UTC
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.intake.router import route_customer_message, route_customer_message_with_context
from app.observability.langsmith_tracing import traceable_if_enabled


class ConversationMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime


class IntakeSession(BaseModel):
    intake_session_id: str
    original_message: str
    latest_message: str
    conversation_messages: list[ConversationMessage] = Field(default_factory=list)
    intent: str
    confidence: float | None = None
    product_type: str | None = None
    product_issue: str | None = None
    damage_type: str | None = None
    customer_id: str | None = None
    order_id: str | None = None
    requires_order_lookup: bool = False
    requires_policy_lookup: bool = False
    missing_fields: list[str] = Field(default_factory=list)
    invalid_fields: list[str] = Field(default_factory=list)
    requires_clarification: bool = False
    next_question: str | None = None
    routed_workflow: str | None = None
    routing_status: str
    error_message: str | None = None
    can_start_workflow: bool = False
    created_at: datetime
    updated_at: datetime


INTAKE_SESSIONS: dict[str, IntakeSession] = {}


def _now() -> datetime:
    return datetime.now(UTC)


def _router_fields(router_output: dict[str, Any]) -> dict[str, Any]:
    return {
        "intent": router_output["intent"],
        "confidence": router_output.get("confidence"),
        "product_type": router_output.get("product_type"),
        "product_issue": router_output.get("product_issue"),
        "damage_type": router_output.get("damage_type"),
        "customer_id": router_output.get("customer_id"),
        "order_id": router_output.get("order_id"),
        "requires_order_lookup": router_output["requires_order_lookup"],
        "requires_policy_lookup": router_output["requires_policy_lookup"],
        "missing_fields": router_output.get("missing_fields", []),
        "invalid_fields": router_output.get("invalid_fields", []),
        "requires_clarification": router_output["requires_clarification"],
        "next_question": router_output.get("next_question"),
        "routed_workflow": router_output.get("routed_workflow"),
        "routing_status": router_output["routing_status"],
        "error_message": router_output.get("error_message"),
        "can_start_workflow": router_output["can_start_workflow"],
    }


def _session_context(session: IntakeSession) -> dict[str, Any]:
    return {
        "intent": session.intent,
        "confidence": session.confidence,
        "product_type": session.product_type,
        "product_issue": session.product_issue,
        "damage_type": session.damage_type,
        "customer_id": session.customer_id,
        "order_id": session.order_id,
    }


def _append_router_question(
    conversation_messages: list[ConversationMessage],
    next_question: str | None,
) -> None:
    if next_question:
        conversation_messages.append(
            ConversationMessage(
                role="router",
                content=next_question,
                timestamp=_now(),
            )
        )


@traceable_if_enabled(name="intake_session_start")
def create_intake_session(message: str) -> IntakeSession:
    timestamp = _now()
    router_output = route_customer_message(message)
    conversation_messages = [
        ConversationMessage(
            role="user",
            content=message,
            timestamp=timestamp,
        )
    ]
    _append_router_question(conversation_messages, router_output.get("next_question"))

    session = IntakeSession(
        intake_session_id=f"intake_{uuid4().hex}",
        original_message=message,
        latest_message=message,
        conversation_messages=conversation_messages,
        created_at=timestamp,
        updated_at=_now(),
        **_router_fields(router_output),
    )
    INTAKE_SESSIONS[session.intake_session_id] = session
    return session


@traceable_if_enabled(name="intake_session_reply")
def update_intake_session(
    intake_session_id: str,
    message: str,
) -> IntakeSession | None:
    session = INTAKE_SESSIONS.get(intake_session_id)
    if session is None:
        return None

    router_output = route_customer_message_with_context(
        message,
        existing_context=_session_context(session),
    )
    updates = _router_fields(router_output)
    conversation_messages = list(session.conversation_messages)
    conversation_messages.append(
        ConversationMessage(
            role="user",
            content=message,
            timestamp=_now(),
        )
    )
    _append_router_question(conversation_messages, router_output.get("next_question"))

    updated = session.model_copy(
        update={
            **updates,
            "latest_message": message,
            "conversation_messages": conversation_messages,
            "updated_at": _now(),
        }
    )
    INTAKE_SESSIONS[intake_session_id] = updated
    return updated


def get_intake_session(intake_session_id: str) -> IntakeSession | None:
    return INTAKE_SESSIONS.get(intake_session_id)


def clear_intake_sessions() -> None:
    INTAKE_SESSIONS.clear()
