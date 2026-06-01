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
    assert "Natural Language Intake" in response.text
    assert "Reply / Continue" in response.text
    assert "Conversation" in response.text
    assert "Router Output" in response.text
    assert "Missing Info Scenario" in response.text
    assert "Complete Cracked Screen Scenario" in response.text
    assert "Eligible Manufacturing Defect Scenario" in response.text
    assert "Unknown Customer Scenario" in response.text
    assert "Invalid Identifier Scenario" in response.text
    assert "Analyze Request" in response.text
    assert "Run Governed Workflow" in response.text
    assert "LangSmith Tracing" in response.text
    assert "Trace Context" in response.text
    assert "Correlation ID" in response.text
    assert 'id="analyze-intake-button"' in response.text
    assert "/static/app.js?v=phase2-correlation-id-1" in response.text
    assert "Optional Workflow Context" not in response.text
    assert "Use optional workflow context when analyzing request" not in response.text
    assert "Clear Context" not in response.text
    assert 'id="use-context"' not in response.text
    assert "Context sent to router" not in response.text
    assert 'id="customer-request"' not in response.text
    assert "Customer Intake" not in response.text


def test_frontend_static_assets_are_served(client: TestClient) -> None:
    css_response = client.get("/static/styles.css")
    js_response = client.get("/static/app.js")

    assert css_response.status_code == 200
    assert js_response.status_code == 200
    assert "telemetry-grid" in css_response.text
    assert "refreshWorkflowView" in js_response.text
    assert "analyze-intake-button" in js_response.text
    assert "reply-intake-button" in js_response.text
    assert "/api/intake/session/start" in js_response.text
    assert "/api/observability/status" in js_response.text
    assert "correlation_id: appState.correlationId" in js_response.text
    assert "renderTraceContextTiles" in js_response.text
    assert "<strong>Correlation:</strong>" in js_response.text
    assert "meta-label\">Correlation" in js_response.text
    assert "Trace links will appear in a future enhancement" in js_response.text
    assert "https://smith.langchain.com" not in js_response.text
    assert "/reply" in js_response.text
    assert "getContextPayload" in js_response.text
    assert "customer_id: null" in js_response.text
    assert "order_id: null" in js_response.text
    assert "clearContext" not in js_response.text
    assert "Extracted Customer ID" in js_response.text
    assert "Extracted Order ID" in js_response.text
    assert "Invalid identifier format" in js_response.text
    assert "cust_unknown_001" in js_response.text
    assert "ord_laptop_power_001" in js_response.text
    assert "UNKNOWN_CUSTOMER" in js_response.text


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
