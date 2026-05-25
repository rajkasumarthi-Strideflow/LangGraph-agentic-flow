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


def test_get_workflow_returns_final_state(client: TestClient) -> None:
    started = _start_workflow(client)

    response = client.get(f"/api/workflows/{started['workflow_id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["workflow_id"] == started["workflow_id"]
    assert data["state"]["workflow_status"] == "completed"
    assert data["state"]["eligibility_status"] == "not_eligible"


def test_get_workflow_audit_returns_timeline(client: TestClient) -> None:
    started = _start_workflow(client)

    response = client.get(f"/api/workflows/{started['workflow_id']}/audit")

    assert response.status_code == 200
    data = response.json()
    event_types = [event["event_type"] for event in data["events"]]
    assert data["workflow_id"] == started["workflow_id"]
    assert "workflow_started" in event_types
    assert "workflow_completed" in event_types


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
