from fastapi.testclient import TestClient

from app.audit.human_review_store import clear_human_reviews
from app.audit.store import clear_audit_events
from sqlalchemy import inspect

from app.database import Base, engine, init_db
from app.main import app
from app.models.db import AuditEventORM, HumanReviewORM, WorkflowRunORM
from app.workflow.store import clear_workflow_results, get_workflow_result


def _clear_tables() -> None:
    clear_human_reviews()
    clear_audit_events()
    clear_workflow_results()


def _start_workflow(
    client: TestClient,
    customer_id: str = "cust_primary_001",
) -> dict:
    response = client.post(
        "/api/workflows/start",
        json={
            "customer_request": "My laptop screen cracked after 9 months. Can I get a replacement?",
            "customer_id": customer_id,
            "order_id": "ord_laptop_001",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_database_initialization_creates_tables() -> None:
    init_db()

    table_names = set(Base.metadata.tables)
    assert "workflow_runs" in table_names
    assert "audit_events" in table_names
    assert "human_reviews" in table_names

    inspector = inspect(engine)
    assert inspector.has_table(WorkflowRunORM.__tablename__)
    assert inspector.has_table(AuditEventORM.__tablename__)
    assert inspector.has_table(HumanReviewORM.__tablename__)


def test_workflow_and_audit_are_persisted() -> None:
    _clear_tables()
    client = TestClient(app)

    started = _start_workflow(client)
    workflow_id = started["workflow_id"]

    persisted_state = get_workflow_result(workflow_id)
    assert persisted_state is not None
    assert persisted_state["eligibility_status"] == "not_eligible"
    assert persisted_state["guardrail_decision"] == "block"

    state_response = client.get(f"/api/workflows/{workflow_id}")
    assert state_response.status_code == 200
    assert state_response.json()["state"]["eligibility_status"] == "not_eligible"

    audit_response = client.get(f"/api/workflows/{workflow_id}/audit")
    assert audit_response.status_code == 200
    events = audit_response.json()["events"]
    event_types = [event["event_type"] for event in events]
    assert "guardrail_decision" in event_types
    assert "replacement_request_created" not in event_types
    guardrail_event = next(
        event for event in events if event["event_type"] == "guardrail_decision"
    )
    assert guardrail_event["guardrail_decision"] == "block"


def test_human_review_is_persisted_for_escalated_workflow() -> None:
    _clear_tables()
    client = TestClient(app)

    started = _start_workflow(client, customer_id="UNKNOWN_CUSTOMER")
    workflow_id = started["workflow_id"]

    review_response = client.post(
        f"/api/workflows/{workflow_id}/human-review",
        json={
            "decision": "request_more_info",
            "reviewer_id": "reviewer_db_001",
            "reason": "Need verified customer identity.",
        },
    )
    assert review_response.status_code == 200
    assert review_response.json()["status"] == "completed"

    reviews_response = client.get(f"/api/workflows/{workflow_id}/human-reviews")
    assert reviews_response.status_code == 200
    reviews = reviews_response.json()["reviews"]
    assert len(reviews) == 1
    assert reviews[0]["workflow_id"] == workflow_id
    assert reviews[0]["reviewer_id"] == "reviewer_db_001"
    assert reviews[0]["decision"] == "request_more_info"


def test_existing_endpoints_still_work_and_unknown_ids_404() -> None:
    _clear_tables()
    client = TestClient(app)

    assert client.get("/health").status_code == 200
    assert client.get("/").status_code == 200
    assert client.get("/api/workflows/wf_missing").status_code == 404
    assert client.get("/api/workflows/wf_missing/audit").status_code == 404
