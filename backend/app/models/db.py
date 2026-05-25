from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utc_now() -> datetime:
    return datetime.now(UTC)


class WorkflowRunORM(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    correlation_id: Mapped[str] = mapped_column(String, index=True)
    workflow_status: Mapped[str] = mapped_column(String)
    customer_id: Mapped[str] = mapped_column(String)
    order_id: Mapped[str] = mapped_column(String)
    final_state: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=_utc_now,
        onupdate=_utc_now,
    )


class AuditEventORM(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    workflow_id: Mapped[str] = mapped_column(String, index=True)
    correlation_id: Mapped[str] = mapped_column(String, index=True)
    event_type: Mapped[str] = mapped_column(String, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    actor: Mapped[str] = mapped_column(String)
    node_name: Mapped[str | None] = mapped_column(String, nullable=True)
    tool_name: Mapped[str | None] = mapped_column(String, nullable=True)
    input_summary: Mapped[dict[str, Any]] = mapped_column(JSON)
    output_summary: Mapped[dict[str, Any]] = mapped_column(JSON)
    policy_reference: Mapped[str | None] = mapped_column(String, nullable=True)
    guardrail_decision: Mapped[str | None] = mapped_column(String, nullable=True)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (
        Index("ix_audit_events_workflow_timestamp", "workflow_id", "timestamp", "id"),
    )


class HumanReviewORM(Base):
    __tablename__ = "human_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String, index=True)
    escalation_id: Mapped[str | None] = mapped_column(String, nullable=True)
    reviewer_id: Mapped[str] = mapped_column(String)
    decision: Mapped[str] = mapped_column(String)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utc_now)
