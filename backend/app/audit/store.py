from app.audit.events import AuditEvent


AUDIT_EVENTS: list[AuditEvent] = []


def record_audit_event(event: AuditEvent) -> AuditEvent:
    AUDIT_EVENTS.append(event)
    return event


def get_audit_events(workflow_id: str) -> list[AuditEvent]:
    return [event for event in AUDIT_EVENTS if event.workflow_id == workflow_id]


def clear_audit_events() -> None:
    AUDIT_EVENTS.clear()
