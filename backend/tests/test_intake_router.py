import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.intake.router import route_customer_message
from app.intake.session import clear_intake_sessions
from app.intake.validator import validate_router_output
from app.main import app
from app.tools.mock_data import PRIMARY_CUSTOMER_ID, PRIMARY_ORDER_ID
from app.tools.mock_data import ELIGIBLE_POWER_ORDER_ID


@pytest.fixture(autouse=True)
def disable_openai_intake(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)
    monkeypatch.setattr(settings, "OPENAI_MODEL", None)
    clear_intake_sessions()


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
    assert result["invalid_fields"] == []
    assert result["customer_id"] == PRIMARY_CUSTOMER_ID
    assert result["order_id"] == PRIMARY_ORDER_ID
    assert result["can_start_workflow"] is True
    assert result["routed_workflow"] == "warranty_replacement"
    assert result["routing_status"] == "fallback_routed"


def test_router_extracts_but_rejects_invalid_identifier_formats() -> None:
    result = route_customer_message(
        "My laptop screen cracked. customer id is 12345 and order id is 776644",
    )

    assert result["customer_id"] == "12345"
    assert result["order_id"] == "776644"
    assert result["requires_clarification"] is True
    assert result["missing_fields"] == []
    assert result["invalid_fields"] == ["customer_id", "order_id"]
    assert result["routed_workflow"] == "warranty_replacement"
    assert result["can_start_workflow"] is False
    assert "valid customer ID and order ID" in result["next_question"]


def test_router_rejects_unknown_customer_literal_format() -> None:
    result = route_customer_message(
        "I need a replacement for my laptop. Customer ID is UNKNOWN_CUSTOMER and order ID is ord_laptop_001.",
    )

    assert result["customer_id"] == "UNKNOWN_CUSTOMER"
    assert result["order_id"] == PRIMARY_ORDER_ID
    assert result["requires_clarification"] is True
    assert result["missing_fields"] == []
    assert result["invalid_fields"] == ["customer_id"]
    assert result["can_start_workflow"] is False


def test_router_allows_syntactically_valid_unknown_customer() -> None:
    result = route_customer_message(
        "I need a replacement for my laptop. Customer ID is cust_unknown_001 and order ID is ord_laptop_001.",
    )

    assert result["customer_id"] == "cust_unknown_001"
    assert result["order_id"] == PRIMARY_ORDER_ID
    assert result["requires_clarification"] is False
    assert result["missing_fields"] == []
    assert result["invalid_fields"] == []
    assert result["can_start_workflow"] is True


def test_router_extracts_primary_mock_ids_from_complete_prompt() -> None:
    result = route_customer_message(
        "My laptop screen broke. Can I get a replacement? "
        f"customer id is {PRIMARY_CUSTOMER_ID} and order id is {PRIMARY_ORDER_ID}",
    )

    assert result["customer_id"] == PRIMARY_CUSTOMER_ID
    assert result["order_id"] == PRIMARY_ORDER_ID
    assert result["requires_clarification"] is False
    assert result["missing_fields"] == []
    assert result["invalid_fields"] == []
    assert result["can_start_workflow"] is True


def test_router_extracts_eligible_power_failure_prompt() -> None:
    result = route_customer_message(
        "My laptop stopped powering on after 6 months. Can I get a replacement? "
        f"Customer ID is {PRIMARY_CUSTOMER_ID} and order ID is {ELIGIBLE_POWER_ORDER_ID}.",
    )

    assert result["intent"] == "warranty_replacement_request"
    assert result["product_type"] == "laptop"
    assert result["product_issue"] == "power_failure"
    assert result["damage_type"] == "manufacturing_defect"
    assert result["customer_id"] == PRIMARY_CUSTOMER_ID
    assert result["order_id"] == ELIGIBLE_POWER_ORDER_ID
    assert result["requires_clarification"] is False
    assert result["missing_fields"] == []
    assert result["invalid_fields"] == []
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
    assert data["invalid_fields"] == []
    assert data["can_start_workflow"] is False


def test_intake_route_api_returns_embedded_customer_and_order_ids() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/intake/route",
        json={
            "message": (
                "My laptop screen broke. Can I get a replacement? "
                f"customer id is {PRIMARY_CUSTOMER_ID} and order id is {PRIMARY_ORDER_ID}"
            ),
            "customer_id": None,
            "order_id": None,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == PRIMARY_CUSTOMER_ID
    assert data["order_id"] == PRIMARY_ORDER_ID
    assert data["requires_clarification"] is False
    assert data["invalid_fields"] == []
    assert data["can_start_workflow"] is True


def test_intake_session_start_requires_clarification_without_ids() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/intake/session/start",
        json={
            "message": "My laptop screen cracked after 9 months. Can I get a replacement?",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["intake_session_id"].startswith("intake_")
    assert data["correlation_id"].startswith("corr_")
    assert data["original_message"] == "My laptop screen cracked after 9 months. Can I get a replacement?"
    assert data["requires_clarification"] is True
    assert data["missing_fields"] == ["customer_id", "order_id"]
    assert data["can_start_workflow"] is False
    assert any(message["role"] == "router" for message in data["conversation_messages"])


def test_intake_session_reply_collects_missing_identifiers() -> None:
    client = TestClient(app)
    start_response = client.post(
        "/api/intake/session/start",
        json={
            "message": "My laptop screen cracked after 9 months. Can I get a replacement?",
        },
    )
    session_id = start_response.json()["intake_session_id"]
    correlation_id = start_response.json()["correlation_id"]

    reply_response = client.post(
        f"/api/intake/session/{session_id}/reply",
        json={
            "message": f"Customer ID is {PRIMARY_CUSTOMER_ID} and order ID is {PRIMARY_ORDER_ID}.",
        },
    )

    assert reply_response.status_code == 200
    data = reply_response.json()
    assert data["intake_session_id"] == session_id
    assert data["correlation_id"] == correlation_id
    assert data["original_message"] == "My laptop screen cracked after 9 months. Can I get a replacement?"
    assert data["intent"] == "warranty_replacement_request"
    assert data["product_issue"] == "cracked_screen"
    assert data["customer_id"] == PRIMARY_CUSTOMER_ID
    assert data["order_id"] == PRIMARY_ORDER_ID
    assert data["requires_clarification"] is False
    assert data["missing_fields"] == []
    assert data["invalid_fields"] == []
    assert data["can_start_workflow"] is True
    assert len(data["conversation_messages"]) >= 3

    get_response = client.get(f"/api/intake/session/{session_id}")
    assert get_response.status_code == 200
    assert get_response.json()["correlation_id"] == correlation_id


def test_intake_session_invalid_identifier_reply_remains_blocked() -> None:
    client = TestClient(app)
    start_response = client.post(
        "/api/intake/session/start",
        json={
            "message": "My laptop screen cracked after 9 months. Can I get a replacement?",
        },
    )
    session_id = start_response.json()["intake_session_id"]

    reply_response = client.post(
        f"/api/intake/session/{session_id}/reply",
        json={
            "message": "Customer ID is UNKNOWN_CUSTOMER and order ID is ord_laptop_001.",
        },
    )

    assert reply_response.status_code == 200
    data = reply_response.json()
    assert data["customer_id"] == "UNKNOWN_CUSTOMER"
    assert data["order_id"] == PRIMARY_ORDER_ID
    assert data["requires_clarification"] is True
    assert data["invalid_fields"] == ["customer_id"]
    assert data["can_start_workflow"] is False


def test_intake_session_valid_unknown_customer_can_route() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/intake/session/start",
        json={
            "message": "I need a replacement for my laptop. Customer ID is cust_unknown_001 and order ID is ord_laptop_001.",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == "cust_unknown_001"
    assert data["order_id"] == PRIMARY_ORDER_ID
    assert data["requires_clarification"] is False
    assert data["can_start_workflow"] is True
    assert "eligibility_status" not in data
    assert "guardrail_decision" not in data
    assert "replacement_request_id" not in data


def test_intake_session_not_found_returns_404() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/intake/session/intake_missing/reply",
        json={"message": "Customer ID is cust_primary_001."},
    )

    assert response.status_code == 404
