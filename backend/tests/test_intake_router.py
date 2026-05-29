import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.intake.router import route_customer_message
from app.intake.validator import validate_router_output
from app.main import app
from app.tools.mock_data import PRIMARY_CUSTOMER_ID, PRIMARY_ORDER_ID


@pytest.fixture(autouse=True)
def disable_openai_intake(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)
    monkeypatch.setattr(settings, "OPENAI_MODEL", None)


def test_deterministic_fallback_classifies_cracked_screen() -> None:
    result = route_customer_message(
        "My laptop screen cracked after 9 months. Can I get a replacement?",
    )

    assert result["intent"] == "warranty_replacement_request"
    assert result["product_type"] == "laptop"
    assert result["product_issue"] == "cracked_screen"
    assert result["damage_type"] == "possible_accidental_damage"
    assert result["routing_status"] == "fallback_clarification_required"


def test_router_identifies_missing_customer_and_order() -> None:
    result = route_customer_message(
        "My laptop screen cracked after 9 months. Can I get a replacement?",
    )

    assert result["requires_clarification"] is True
    assert result["missing_fields"] == ["customer_id", "order_id"]
    assert result["can_start_workflow"] is False
    assert "customer ID" in result["next_question"]
    assert result["routed_workflow"] == "warranty_replacement"


def test_router_routes_when_customer_and_order_are_provided() -> None:
    result = route_customer_message(
        "My laptop screen cracked after 9 months. Can I get a replacement?",
        customer_id=PRIMARY_CUSTOMER_ID,
        order_id=PRIMARY_ORDER_ID,
    )

    assert result["requires_clarification"] is False
    assert result["missing_fields"] == []
    assert result["customer_id"] == PRIMARY_CUSTOMER_ID
    assert result["order_id"] == PRIMARY_ORDER_ID
    assert result["can_start_workflow"] is True
    assert result["routed_workflow"] == "warranty_replacement"
    assert result["routing_status"] == "fallback_routed"


def test_router_extracts_customer_and_order_ids_from_message() -> None:
    result = route_customer_message(
        "My laptop screen cracked. customer id is 12345 and order id is 776644",
    )

    assert result["customer_id"] == "12345"
    assert result["order_id"] == "776644"
    assert result["requires_clarification"] is False
    assert result["missing_fields"] == []
    assert result["routed_workflow"] == "warranty_replacement"
    assert result["can_start_workflow"] is True


def test_router_does_not_output_decision_or_action_fields() -> None:
    result = route_customer_message(
        "My laptop screen cracked after 9 months. Can I get a replacement?",
        customer_id=PRIMARY_CUSTOMER_ID,
        order_id=PRIMARY_ORDER_ID,
    )

    assert "eligibility_status" not in result
    assert "guardrail_decision" not in result
    assert "replacement_request_id" not in result


def test_validator_blocks_decision_and_action_fields() -> None:
    validation = validate_router_output(
        {
            "intent": "warranty_replacement_request",
            "confidence": 0.9,
            "routed_workflow": "warranty_replacement",
            "eligibility_status": "eligible",
            "guardrail_decision": "allow",
            "replacement_request_id": "rr_123",
            "next_question": "Your replacement request is approved.",
        }
    )

    assert validation["validation_status"] == "failed"
    assert any("eligibility_status" in error for error in validation["validation_errors"])
    assert any("guardrail_decision" in error for error in validation["validation_errors"])
    assert any("replacement_request_id" in error for error in validation["validation_errors"])
    assert any("approval" in error for error in validation["validation_errors"])


def test_intake_route_api_returns_router_output() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/intake/route",
        json={
            "message": "My laptop screen cracked after 9 months. Can I get a replacement?",
            "customer_id": PRIMARY_CUSTOMER_ID,
            "order_id": PRIMARY_ORDER_ID,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "warranty_replacement_request"
    assert data["routed_workflow"] == "warranty_replacement"
    assert data["requires_clarification"] is False
    assert data["can_start_workflow"] is True


def test_intake_route_api_requires_clarification_without_ids() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/intake/route",
        json={
            "message": "My laptop screen cracked after 9 months. Can I get a replacement?",
            "customer_id": None,
            "order_id": None,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "warranty_replacement_request"
    assert data["requires_clarification"] is True
    assert data["missing_fields"] == ["customer_id", "order_id"]
    assert data["can_start_workflow"] is False
