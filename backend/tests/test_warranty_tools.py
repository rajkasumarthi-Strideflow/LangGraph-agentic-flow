from app.tools.mock_data import (
    CURRENT_LAPTOP_POLICY_ID,
    PRIMARY_CUSTOMER_ID,
    PRIMARY_ORDER_ID,
    PRIMARY_PRODUCT_ID,
)
from app.tools.warranty_tools import (
    check_inventory_availability,
    check_replacement_eligibility,
    create_replacement_request,
    escalate_to_human,
    generate_customer_response,
    lookup_order,
    retrieve_warranty_policy,
    verify_identity,
)


def test_verify_identity_succeeds_for_primary_customer() -> None:
    result = verify_identity(PRIMARY_CUSTOMER_ID)

    assert result["result_status"] == "success"
    assert result["customer_id"] == PRIMARY_CUSTOMER_ID
    assert result["identity_verified"] is True


def test_verify_identity_fails_for_unknown_customer() -> None:
    result = verify_identity("cust_unknown")

    assert result["result_status"] == "not_found"
    assert result["customer_id"] == "cust_unknown"
    assert result["identity_verified"] is False


def test_lookup_order_succeeds_for_primary_customer_and_order() -> None:
    result = lookup_order(PRIMARY_CUSTOMER_ID, PRIMARY_ORDER_ID)

    assert result["result_status"] == "success"
    assert result["order_id"] == PRIMARY_ORDER_ID
    assert result["customer_id"] == PRIMARY_CUSTOMER_ID
    assert result["product_id"] == PRIMARY_PRODUCT_ID
    assert result["product_family"] == "laptop"
    assert result["order_status"] == "delivered"
    assert result["purchase_age_months"] == 9


def test_lookup_order_returns_authorization_error_for_wrong_customer() -> None:
    result = lookup_order("cust_wrong", PRIMARY_ORDER_ID)

    assert result["result_status"] == "authorization_error"
    assert result["order_id"] == PRIMARY_ORDER_ID


def test_retrieve_warranty_policy_returns_current_policy() -> None:
    result = retrieve_warranty_policy(product_family="laptop", region="US")

    assert result["result_status"] == "success"
    assert result["policy_id"] == CURRENT_LAPTOP_POLICY_ID
    assert result["status"] == "current"
    assert result["product_family"] == "laptop"
    assert result["region"] == "US"


def test_check_replacement_eligibility_returns_not_eligible_for_cracked_screen() -> None:
    result = check_replacement_eligibility(
        customer_id=PRIMARY_CUSTOMER_ID,
        order_id=PRIMARY_ORDER_ID,
        policy_id=CURRENT_LAPTOP_POLICY_ID,
    )

    assert result["result_status"] == "success"
    assert result["eligibility_status"] == "not_eligible"
    assert "cracked screens" in result["reason"]


def test_check_replacement_eligibility_includes_policy_reference() -> None:
    result = check_replacement_eligibility(
        customer_id=PRIMARY_CUSTOMER_ID,
        order_id=PRIMARY_ORDER_ID,
        policy_id=CURRENT_LAPTOP_POLICY_ID,
    )

    assert result["policy_reference"] == f"{CURRENT_LAPTOP_POLICY_ID}#v2.0"
    assert result["policy_version"] == "2.0"


def test_check_inventory_availability_returns_available_primary_inventory() -> None:
    result = check_inventory_availability(PRIMARY_PRODUCT_ID)

    assert result["result_status"] == "success"
    assert result["product_id"] == PRIMARY_PRODUCT_ID
    assert result["inventory_available"] is True
    assert result["inventory_status"] == "available"
    assert result["available_quantity"] == 5


def test_create_replacement_request_blocked_when_not_eligible() -> None:
    result = create_replacement_request(
        customer_id=PRIMARY_CUSTOMER_ID,
        order_id=PRIMARY_ORDER_ID,
        product_id=PRIMARY_PRODUCT_ID,
        eligibility_status="not_eligible",
        inventory_available=True,
    )

    assert result["result_status"] == "blocked_by_guardrail"
    assert result["replacement_status"] == "not_created"
    assert "eligibility is approved" in result["reason"]


def test_create_replacement_request_succeeds_when_eligible_and_inventory_available() -> None:
    result = create_replacement_request(
        customer_id=PRIMARY_CUSTOMER_ID,
        order_id=PRIMARY_ORDER_ID,
        product_id=PRIMARY_PRODUCT_ID,
        eligibility_status="eligible",
        inventory_available=True,
    )

    assert result["result_status"] == "success"
    assert result["replacement_status"] == "created"
    assert result["replacement_request_id"]


def test_escalate_to_human_returns_open_escalation() -> None:
    result = escalate_to_human(
        customer_id=PRIMARY_CUSTOMER_ID,
        order_id=PRIMARY_ORDER_ID,
        reason="Policy conflict requires review.",
    )

    assert result["result_status"] == "success"
    assert result["escalation_status"] == "open"
    assert result["escalation_id"]
    assert result["customer_id"] == PRIMARY_CUSTOMER_ID


def test_generate_customer_response_does_not_claim_replacement_without_request_id() -> None:
    result = generate_customer_response(
        eligibility_status="eligible",
        replacement_request_id=None,
        escalation_id=None,
        reason="Eligibility passed, but no replacement request was created.",
    )

    assert result["response_type"] == "informational"
    assert "replacement request has been created" not in result["customer_response"]


def test_generate_customer_response_handles_escalation() -> None:
    result = generate_customer_response(
        eligibility_status="human_review_required",
        replacement_request_id=None,
        escalation_id="esc_123",
        reason="Policy conflict requires review.",
    )

    assert result["response_type"] == "human_review"
    assert "routed for human review" in result["customer_response"]
    assert "esc_123" in result["customer_response"]


def test_generate_customer_response_handles_not_eligible() -> None:
    result = generate_customer_response(
        eligibility_status="not_eligible",
        replacement_request_id=None,
        escalation_id=None,
        reason="Accidental damage is excluded.",
    )

    assert result["response_type"] == "not_eligible"
    assert "not automatically eligible" in result["customer_response"]
    assert "replacement request has been created" not in result["customer_response"]
