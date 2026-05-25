from app.audit.events import AuditEvent
from app.database import SessionLocal, init_db
from app.models.db import AuditEventORM


def record_audit_event(event: AuditEvent) -> AuditEvent:
    init_db()
    with SessionLocal() as db:
        db_event = AuditEventORM(
            event_id=event.event_id,
            workflow_id=event.workflow_id,
            correlation_id=event.correlation_id,
            event_type=event.event_type,
            timestamp=event.timestamp,
            actor=event.actor,
            node_name=event.node_name,
            tool_name=event.tool_name,
            input_summary=event.input_summary,
            output_summary=event.output_summary,
            policy_reference=event.policy_reference,
            guardrail_decision=event.guardrail_decision,
            reason=event.reason,
        )
        db.add(db_event)
        db.commit()
    return event


def get_audit_events(workflow_id: str) -> list[AuditEvent]:
    init_db()
    with SessionLocal() as db:
        rows = (
            db.query(AuditEventORM)
            .filter(AuditEventORM.workflow_id == workflow_id)
            .order_by(AuditEventORM.timestamp.asc(), AuditEventORM.id.asc())
            .all()
        )
        return [
            AuditEvent(
                event_id=row.event_id,
                workflow_id=row.workflow_id,
                correlation_id=row.correlation_id,
                event_type=row.event_type,
                timestamp=row.timestamp,
                actor=row.actor,
                node_name=row.node_name,
                tool_name=row.tool_name,
                input_summary=row.input_summary,
                output_summary=row.output_summary,
                policy_reference=row.policy_reference,
                guardrail_decision=row.guardrail_decision,
                reason=row.reason,
            )
            for row in rows
        ]


def clear_audit_events() -> None:
    init_db()
    with SessionLocal() as db:
        db.query(AuditEventORM).delete()
        db.commit()
