from __future__ import annotations

from typing import Any


SHIPMENT_CLAIM_TERMS = [
    "shipment is on the way",
    "shipment has been created",
    "has been shipped",
    "is shipped",
    "shipped",
    "tracking number",
    "tracking information",
    "delivery is scheduled",
    "on its way",
]

REPLACEMENT_CREATED_CLAIM_TERMS = [
    "replacement request has been created",
    "replacement has been created",
    "replacement request was created",
    "replacement was created",
    "replacement has been processed",
    "request has been approved",
    "replacement is approved",
]


def _assert_equal(actual: Any, expected: Any, field: str) -> None:
    if expected == "__exists__":
        assert actual, f"{field}: expected a value to exist"
        return
    assert actual == expected, f"{field}: expected {expected!r}, got {actual!r}"


def _assert_includes(values: list[Any] | None, expected_values: list[Any], field: str) -> None:
    actual_values = values or []
    for expected in expected_values:
        assert expected in actual_values, (
            f"{field}: expected to include {expected!r}, got {actual_values!r}"
        )


def assert_intake_expectations(
    result: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    intake_expected = expected.get("intake", {})
    if "requires_clarification" in intake_expected:
        _assert_equal(
            result.get("requires_clarification"),
            intake_expected["requires_clarification"],
            "intake.requires_clarification",
        )
    if "can_start_workflow" in intake_expected:
        _assert_equal(
            result.get("can_start_workflow"),
            intake_expected["can_start_workflow"],
            "intake.can_start_workflow",
        )
    if "missing_fields_includes" in intake_expected:
        _assert_includes(
            result.get("missing_fields"),
            intake_expected["missing_fields_includes"],
            "intake.missing_fields",
        )
    if "missing_fields" in intake_expected:
        _assert_equal(
            result.get("missing_fields"),
            intake_expected["missing_fields"],
            "intake.missing_fields",
        )
    if "invalid_fields_includes" in intake_expected:
        _assert_includes(
            result.get("invalid_fields"),
            intake_expected["invalid_fields_includes"],
            "intake.invalid_fields",
        )
    if "invalid_fields" in intake_expected:
        _assert_equal(
            result.get("invalid_fields"),
            intake_expected["invalid_fields"],
            "intake.invalid_fields",
        )


def assert_no_shipment_claim(response: str | None) -> None:
    normalized = (response or "").lower()
    for term in SHIPMENT_CLAIM_TERMS:
        assert term not in normalized, f"response must not claim shipment: {term!r}"


def assert_no_replacement_claim_when_no_replacement_id(state: dict[str, Any]) -> None:
    if state.get("replacement_request_id"):
        return
    normalized = (state.get("customer_response") or "").lower()
    for term in REPLACEMENT_CREATED_CLAIM_TERMS:
        assert term not in normalized, (
            "response must not claim replacement creation without "
            f"replacement_request_id: {term!r}"
        )


def assert_policy_control_outcome(
    state: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    workflow_expected = expected.get("workflow", {})
    for field in [
        "identity_verified",
        "order_retrieved",
        "eligibility_status",
        "inventory_available",
        "guardrail_decision",
        "replacement_request_id",
        "escalation_id",
    ]:
        if field in workflow_expected:
            _assert_equal(state.get(field), workflow_expected[field], f"workflow.{field}")

    if workflow_expected.get("escalation_id_exists"):
        assert state.get("escalation_id"), "workflow.escalation_id should exist"

    if workflow_expected.get("replacement_request_id_exists"):
        assert state.get("replacement_request_id"), (
            "workflow.replacement_request_id should exist"
        )


def assert_workflow_expectations(
    result: dict[str, Any] | None,
    expected: dict[str, Any],
) -> None:
    workflow_should_start = expected.get("workflow_should_start", False)
    if not workflow_should_start:
        assert result is None, "workflow should not have started"
        return

    assert result is not None, "workflow should have started"
    assert result.get("workflow_status") == "completed", "workflow should complete"

    workflow_expected = expected.get("workflow", {})
    assert_policy_control_outcome(result, expected)

    if workflow_expected.get("response_must_not_claim_shipment"):
        assert_no_shipment_claim(result.get("customer_response"))

    if workflow_expected.get("response_must_not_claim_replacement_created"):
        assert_no_replacement_claim_when_no_replacement_id(result)

    if workflow_expected.get("response_should_explain_verification_or_escalation"):
        response = (result.get("customer_response") or "").lower()
        assert any(term in response for term in ["verification", "human review", "routed"]), (
            "response should explain verification issue or escalation safely"
        )


def assert_eval_result(
    scenario: dict[str, Any],
    intake_result: dict[str, Any],
    workflow_result: dict[str, Any] | None,
) -> None:
    expected = scenario["expected"]
    assert_intake_expectations(intake_result, expected)
    assert_workflow_expectations(workflow_result, expected)
