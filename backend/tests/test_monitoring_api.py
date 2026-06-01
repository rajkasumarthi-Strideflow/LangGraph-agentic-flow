from fastapi.testclient import TestClient

from app.audit.human_review_store import clear_human_reviews
from app.audit.store import clear_audit_events
from app.main import app
from app.tools.mock_data import (
    ELIGIBLE_POWER_ORDER_ID,
    PRIMARY_CUSTOMER_ID,
    PRIMARY_ORDER_ID,
)
from app.workflow.store import clear_workflow_results


def _clear_tables() -> None:
    clear_human_reviews()
    clear_audit_events()
    clear_workflow_results()


def _start_workflow(
    client: TestClient,
    *,
    customer_id: str = PRIMARY_CUSTOMER_ID,
    order_id: str = PRIMARY_ORDER_ID,
    customer_request: str = "My laptop screen cracked after 9 months. Can I get a replacement?",
) -> dict:
    response = client.post(
        "/api/workflows/start",
        json={
            "customer_request": customer_request,
            "customer_id": customer_id,
            "order_id": order_id,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_monitoring_summary_returns_zero_counts_without_runs() -> None:
    _clear_tables()
    client = TestClient(app)

    response = client.get("/api/monitoring/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["total_workflow_runs"] == 0
    assert data["blocked_count"] == 0
    assert data["total_audit_events"] == 0
    assert data["total_tool_calls"] == 0


def test_monitoring_summary_counts_cracked_screen_block() -> None:
    _clear_tables()
    client = TestClient(app)
    _start_workflow(client)

    response = client.get("/api/monitoring/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["total_workflow_runs"] == 1
    assert data["blocked_count"] == 1
    assert data["replacement_request_count"] == 0
    assert data["total_audit_events"] > 0
    assert data["total_tool_calls"] > 0


def test_monitoring_summary_counts_eligible_allow_action() -> None:
    _clear_tables()
    client = TestClient(app)
    _start_workflow(
        client,
        order_id=ELIGIBLE_POWER_ORDER_ID,
        customer_request=(
            "My laptop stopped powering on after 6 months. Can I get a replacement?"
        ),
    )

    response = client.get("/api/monitoring/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["allowed_action_count"] == 1
    assert data["replacement_request_count"] == 1
    assert data["outcome_breakdown"]["allowed_action"] == 1


def test_monitoring_summary_counts_unknown_customer_escalation() -> None:
    _clear_tables()
    client = TestClient(app)
    _start_workflow(client, customer_id="cust_unknown_001")

    response = client.get("/api/monitoring/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["escalated_count"] == 1
    assert data["outcome_breakdown"]["escalated"] == 1


def test_monitoring_runs_return_correlation_and_filters() -> None:
    _clear_tables()
    client = TestClient(app)
    blocked = _start_workflow(client)
    allowed = _start_workflow(
        client,
        order_id=ELIGIBLE_POWER_ORDER_ID,
        customer_request=(
            "My laptop stopped powering on after 6 months. Can I get a replacement?"
        ),
    )

    all_response = client.get("/api/monitoring/runs")
    assert all_response.status_code == 200
    runs = all_response.json()["runs"]
    assert len(runs) == 2
    assert {run["outcome"] for run in runs} == {"blocked", "allowed_action"}
    assert all(run["correlation_id"] for run in runs)
    assert all(run["audit_event_count"] > 0 for run in runs)
    assert all(run["tool_call_count"] > 0 for run in runs)

    workflow_type_response = client.get(
        "/api/monitoring/runs?workflow_type=warranty_replacement"
    )
    assert workflow_type_response.status_code == 200
    assert len(workflow_type_response.json()["runs"]) == 2

    outcome_response = client.get("/api/monitoring/runs?outcome=allowed_action")
    assert outcome_response.status_code == 200
    outcome_runs = outcome_response.json()["runs"]
    assert len(outcome_runs) == 1
    assert outcome_runs[0]["workflow_id"] == allowed["workflow_id"]

    correlation_response = client.get(
        f"/api/monitoring/runs?correlation_id={blocked['correlation_id']}"
    )
    assert correlation_response.status_code == 200
    correlation_runs = correlation_response.json()["runs"]
    assert len(correlation_runs) == 1
    assert correlation_runs[0]["workflow_id"] == blocked["workflow_id"]


def test_monitoring_token_totals_use_final_state_values(monkeypatch) -> None:
    _clear_tables()
    client = TestClient(app)

    def fake_draft_customer_response_with_llm(state: dict) -> dict:
        return {
            "drafting_status": "completed",
            "llm_customer_response": (
                "Based on the current policy, this item is not automatically "
                "eligible for replacement."
            ),
            "model_name": "test-model",
            "llm_input_payload": {"eligibility_status": state.get("eligibility_status")},
            "usage": {
                "input_tokens": 12,
                "output_tokens": 8,
                "total_tokens": 20,
                "cached_tokens": 0,
            },
            "error_message": None,
        }

    monkeypatch.setattr(
        "app.workflow.nodes.draft_customer_response_with_llm",
        fake_draft_customer_response_with_llm,
    )
    _start_workflow(client)

    response = client.get("/api/monitoring/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["llm_drafting_completed_count"] == 1
    assert data["total_input_tokens"] == 12
    assert data["total_output_tokens"] == 8
    assert data["total_tokens"] == 20


def test_monitoring_outcomes_endpoint_returns_filters() -> None:
    client = TestClient(app)

    response = client.get("/api/monitoring/outcomes")

    assert response.status_code == 200
    data = response.json()
    assert "warranty_replacement" in data["workflow_types"]
    assert "blocked" in data["outcomes"]
    assert "allowed_action" in data["outcomes"]
