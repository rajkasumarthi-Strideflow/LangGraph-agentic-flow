import pytest
from fastapi.testclient import TestClient

from app.audit.store import clear_audit_events
from app.main import app
from app.workflow.store import clear_workflow_results


@pytest.fixture(autouse=True)
def clear_in_memory_stores() -> None:
    clear_audit_events()
    clear_workflow_results()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_frontend_index_returns_warrantywise(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "WarrantyWise" in response.text


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
