import pytest

from evals.assertions import (
    assert_no_replacement_claim_when_no_replacement_id,
    assert_no_shipment_claim,
)
from evals.runner import (
    load_golden_scenarios,
    run_golden_scenario_evaluations,
)


def test_golden_scenarios_file_loads_successfully() -> None:
    scenarios = load_golden_scenarios()

    assert scenarios
    assert all("id" in scenario for scenario in scenarios)


def test_all_scenario_ids_are_unique() -> None:
    scenarios = load_golden_scenarios()
    scenario_ids = [scenario["id"] for scenario in scenarios]

    assert len(scenario_ids) == len(set(scenario_ids))


def test_all_golden_scenarios_include_expected_fields() -> None:
    scenarios = load_golden_scenarios()

    for scenario in scenarios:
        assert scenario["input"]
        assert "expected" in scenario
        assert "intake" in scenario["expected"]
        assert "workflow_should_start" in scenario["expected"]


def test_local_evaluation_runner_passes_current_golden_scenarios() -> None:
    summary = run_golden_scenario_evaluations()

    assert summary["total_scenarios"] == 5
    assert summary["passed"] == 5
    assert summary["failed"] == 0
    assert summary["failures"] == []


def test_overpromise_assertion_fails_on_shipment_claim() -> None:
    with pytest.raises(AssertionError, match="shipment"):
        assert_no_shipment_claim(
            "Your replacement request has been created and shipment is on the way."
        )


def test_replacement_claim_assertion_fails_without_replacement_id() -> None:
    state = {
        "replacement_request_id": None,
        "customer_response": "Your replacement request has been created.",
    }

    with pytest.raises(AssertionError, match="replacement"):
        assert_no_replacement_claim_when_no_replacement_id(state)
