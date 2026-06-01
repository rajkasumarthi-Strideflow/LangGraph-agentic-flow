import pytest
from fastapi.testclient import TestClient

from app.audit.human_review_store import clear_human_reviews
from app.audit.store import clear_audit_events
from app.main import app
from app.tools.mock_data import PRIMARY_CUSTOMER_ID, PRIMARY_ORDER_ID
from app.workflow.store import clear_workflow_results


@pytest.fixture(autouse=True)
def clear_in_memory_stores() -> None:
    clear_human_reviews()
    clear_audit_events()
    clear_workflow_results()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _start_workflow(
    client: TestClient,
    customer_id: str = PRIMARY_CUSTOMER_ID,
    order_id: str = PRIMARY_ORDER_ID,
) -> dict:
    response = client.post(
        "/api/workflows/start",
        json={
            "customer_request": "My laptop screen cracked after 9 months. Can I get a replacement?",
            "customer_id": customer_id,
            "order_id": order_id,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_start_workflow_primary_cracked_screen(client: TestClient) -> None:
    data = _start_workflow(client)

    assert data["workflow_id"]
    assert data["correlation_id"]
    assert data["workflow_status"] == "completed"
    assert data["eligibility_status"] == "not_eligible"
    assert data["replacement_request_id"] is None
    assert data["customer_response"]
    assert data["llm_drafting_status"] == "not_configured"
    assert data["final_response_source"] == "llm_not_configured_fallback"


def test_get_workflow_returns_final_state(client: TestClient) -> None:
    started = _start_workflow(client)

    response = client.get(f"/api/workflows/{started['workflow_id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["workflow_id"] == started["workflow_id"]
    assert data["correlation_id"] == started["correlation_id"]
    assert data["state"]["workflow_status"] == "completed"
    assert data["state"]["correlation_id"] == started["correlation_id"]
    assert data["state"]["eligibility_status"] == "not_eligible"
    assert data["state"]["llm_drafting_status"] == "not_configured"


def test_get_workflow_audit_returns_timeline(client: TestClient) -> None:
    started = _start_workflow(client)

    response = client.get(f"/api/workflows/{started['workflow_id']}/audit")

    assert response.status_code == 200
    data = response.json()
    event_types = [event["event_type"] for event in data["events"]]
    assert data["workflow_id"] == started["workflow_id"]
    assert data["correlation_id"] == started["correlation_id"]
    assert all(event["correlation_id"] == started["correlation_id"] for event in data["events"])
    assert all(
        event["input_summary"]["correlation_id"] == started["correlation_id"]
        for event in data["events"]
    )
    assert all(
        event["output_summary"]["correlation_id"] == started["correlation_id"]
        for event in data["events"]
    )
    assert "workflow_started" in event_types
    assert "workflow_completed" in event_types


def test_workflow_started_from_intake_reuses_correlation_id(client: TestClient) -> None:
    intake_response = client.post(
        "/api/intake/session/start",
        json={
            "message": (
                "My laptop screen cracked after 9 months. Can I get a replacement? "
                "Customer ID is cust_primary_001 and order ID is ord_laptop_001."
            ),
        },
    )
    assert intake_response.status_code == 200
    intake = intake_response.json()

    workflow_response = client.post(
        "/api/workflows/start",
        json={
            "customer_request": intake["original_message"],
            "customer_id": intake["customer_id"],
            "order_id": intake["order_id"],
            "correlation_id": intake["correlation_id"],
        },
    )
    assert workflow_response.status_code == 200
    workflow = workflow_response.json()
    assert workflow["correlation_id"] == intake["correlation_id"]

    correlation_response = client.get(f"/api/correlation/{intake['correlation_id']}")
    assert correlation_response.status_code == 200
    correlation = correlation_response.json()
    assert correlation["correlation_id"] == intake["correlation_id"]
    assert correlation["intake_session_id"] == intake["intake_session_id"]
    assert correlation["workflow_id"] == workflow["workflow_id"]
    assert correlation["audit_event_count"] > 0
    assert correlation["workflow_status"] == "completed"


def test_direct_workflow_start_generates_correlation_id(client: TestClient) -> None:
    started = _start_workflow(client)

    assert started["correlation_id"].startswith("corr_")
    audit_response = client.get(f"/api/workflows/{started['workflow_id']}/audit")
    assert audit_response.status_code == 200
    events = audit_response.json()["events"]
    assert events
    assert all(event["correlation_id"] == started["correlation_id"] for event in events)


def test_unknown_workflow_returns_404_for_state(client: TestClient) -> None:
    response = client.get("/api/workflows/wf_unknown")

    assert response.status_code == 404


def test_unknown_workflow_returns_404_for_audit(client: TestClient) -> None:
    response = client.get("/api/workflows/wf_unknown/audit")

    assert response.status_code == 404


def test_human_review_endpoint_handles_escalated_workflow(client: TestClient) -> None:
    started = _start_workflow(client, customer_id="cust_unknown")

    response = client.post(
        f"/api/workflows/{started['workflow_id']}/human-review",
        json={
            "decision": "manual_review_completed",
            "reviewer_id": "reviewer_001",
            "reason": "Customer identity could not be verified.",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["workflow_id"] == started["workflow_id"]
    assert data["status"] == "completed"
    assert data["reviewer_id"] == "reviewer_001"

    reviews_response = client.get(
        f"/api/workflows/{started['workflow_id']}/human-reviews"
    )
    assert reviews_response.status_code == 200
    reviews = reviews_response.json()["reviews"]
    assert len(reviews) == 1
    assert reviews[0]["reviewer_id"] == "reviewer_001"
    assert reviews[0]["decision"] == "manual_review_completed"


def test_human_review_endpoint_reports_no_review_required(
    client: TestClient,
) -> None:
    started = _start_workflow(client)

    response = client.post(
        f"/api/workflows/{started['workflow_id']}/human-review",
        json={
            "decision": "approve",
            "reviewer_id": "reviewer_001",
            "reason": "Testing no-review path.",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_required"
    assert "No human review" in data["message"]


def test_unknown_workflow_returns_404_for_human_reviews(client: TestClient) -> None:
    response = client.get("/api/workflows/wf_unknown/human-reviews")

    assert response.status_code == 404
