from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.observability.langsmith_tracing import get_langsmith_status, is_langsmith_enabled
from app.tools.mock_data import PRIMARY_CUSTOMER_ID, PRIMARY_ORDER_ID
from app.workflow.graph import run_warranty_workflow


def _base_state(customer_id: str, order_id: str) -> dict:
    return {
        "workflow_id": "wf_observability_test",
        "correlation_id": "corr_observability_test",
        "customer_request": "My laptop screen cracked after 9 months. Can I get a replacement?",
        "customer_id": customer_id,
        "order_id": order_id,
        "product_id": None,
        "product_family": None,
        "identity_verified": False,
        "customer_authorized": False,
        "order_retrieved": False,
        "order_status": None,
        "purchase_age_months": None,
        "policy_id": None,
        "policy_reference": None,
        "policy_version": None,
        "eligibility_status": None,
        "eligibility_reason": None,
        "inventory_available": None,
        "inventory_status": None,
        "replacement_request_id": None,
        "replacement_status": None,
        "escalation_id": None,
        "escalation_required": False,
        "escalation_reason": None,
        "guardrail_decision": None,
        "customer_response": None,
        "response_type": None,
        "llm_drafting_status": None,
        "llm_customer_response": None,
        "llm_model_name": None,
        "llm_input_tokens": None,
        "llm_output_tokens": None,
        "llm_total_tokens": None,
        "llm_cached_tokens": None,
        "llm_validation_status": None,
        "llm_validation_errors": None,
        "final_response_source": None,
        "error_category": None,
        "workflow_status": "started",
    }


def test_langsmith_status_disabled_when_tracing_false(monkeypatch) -> None:
    monkeypatch.setattr(settings, "LANGSMITH_TRACING", False)
    monkeypatch.setattr(settings, "LANGSMITH_API_KEY", "lsv2_secret")

    status = get_langsmith_status()

    assert is_langsmith_enabled() is False
    assert status["tracing_status"] == "disabled"
    assert status["provider"] == "langsmith"
    assert status["project"] == "decisiontrace-phase2"
    assert status["trace_url"] is None
    assert status["trace_url_supported"] is False


def test_langsmith_status_not_configured_without_api_key(monkeypatch) -> None:
    monkeypatch.setattr(settings, "LANGSMITH_TRACING", True)
    monkeypatch.setattr(settings, "LANGSMITH_API_KEY", None)

    status = get_langsmith_status()

    assert is_langsmith_enabled() is False
    assert status["tracing_status"] == "not_configured"


def test_observability_status_api_does_not_expose_api_key(monkeypatch) -> None:
    monkeypatch.setattr(settings, "LANGSMITH_TRACING", True)
    monkeypatch.setattr(settings, "LANGSMITH_API_KEY", "lsv2_do_not_expose")
    monkeypatch.setattr(settings, "LANGSMITH_PROJECT", "decisiontrace-test")
    client = TestClient(app)

    response = client.get("/api/observability/status")

    assert response.status_code == 200
    data = response.json()
    assert data["tracing_status"] == "enabled"
    assert data["project"] == "decisiontrace-test"
    assert "lsv2_do_not_expose" not in response.text
    assert data["trace_url_supported"] is False


def test_workflow_still_completes_when_langsmith_not_configured(monkeypatch) -> None:
    monkeypatch.setattr(settings, "LANGSMITH_TRACING", False)
    monkeypatch.setattr(settings, "LANGSMITH_API_KEY", None)

    result = run_warranty_workflow(
        _base_state(customer_id=PRIMARY_CUSTOMER_ID, order_id=PRIMARY_ORDER_ID)
    )

    assert result["workflow_status"] == "completed"
    assert result["eligibility_status"] == "not_eligible"
