import pytest
from fastapi.testclient import TestClient

from app.audit.human_review_store import clear_human_reviews
from app.audit.store import clear_audit_events
from app.main import app
from app.workflow.store import clear_workflow_results


@pytest.fixture(autouse=True)
def clear_in_memory_stores() -> None:
    clear_human_reviews()
    clear_audit_events()
    clear_workflow_results()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_frontend_index_returns_decisiontrace_branding(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "DecisionTrace AI" in response.text
    assert "Auditable Agentic Workflows for Governed Customer Decisions" in response.text
    assert "Analyze Request" in response.text
    assert 'id="analyze-intake-button"' in response.text


def test_frontend_static_assets_are_served(client: TestClient) -> None:
    css_response = client.get("/static/styles.css")
    js_response = client.get("/static/app.js")

    assert css_response.status_code == 200
    assert js_response.status_code == 200
    assert "telemetry-grid" in css_response.text
    assert "refreshWorkflowView" in js_response.text
    assert "analyze-intake-button" in js_response.text


def test_health_still_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_start_workflow_api_still_works(client: TestClient) -> None:
    response = client.post(
        "/api/workflows/start",
        json={
            "customer_request": "My laptop screen cracked after 9 months. Can I get a replacement?",
            "customer_id": "cust_primary_001",
            "order_id": "ord_laptop_001",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["workflow_status"] == "completed"
    assert data["eligibility_status"] == "not_eligible"
