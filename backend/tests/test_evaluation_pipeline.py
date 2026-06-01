import pytest

from evals.assertions import (
    assert_no_replacement_claim_when_no_replacement_id,
    assert_no_shipment_claim,
)
from evals.runner import (
    load_golden_scenarios,
    run_golden_scenario_evaluations,
)
from evals.langsmith_export import (
    LangSmithEvaluationConfigError,
    golden_scenarios_to_langsmith_examples,
    require_langsmith_evaluation_config,
    run_scenario_for_langsmith,
    scenario_to_langsmith_example,
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
        assert scenario["business_scenario"]
        assert scenario["business_expectation"]
        assert scenario["control_model_expectation"]
        assert scenario["input"]["message"]
        assert "expected" in scenario
        assert "intake" in scenario["expected"]
        assert "workflow_should_start" in scenario["expected"]


def test_local_evaluation_runner_passes_current_golden_scenarios() -> None:
    summary = run_golden_scenario_evaluations()

    assert summary["total_scenarios"] == 5
    assert summary["passed"] == 5
    assert summary["failed"] == 0
    assert summary["failures"] == []


def test_golden_scenario_converts_to_langsmith_example_format() -> None:
    scenario = load_golden_scenarios()[0]

    example = scenario_to_langsmith_example(scenario)

    assert example["inputs"]["scenario_id"] == scenario["id"]
    assert example["inputs"]["message"] == scenario["input"]["message"]
    assert example["outputs"]["business_scenario"] == scenario["business_scenario"]
    assert example["outputs"]["business_expectation"] == scenario["business_expectation"]
    assert (
        example["outputs"]["control_model_expectation"]
        == scenario["control_model_expectation"]
    )
    assert example["outputs"]["expected"] == scenario["expected"]
    assert example["metadata"]["evaluation_type"] == "deterministic_control_model"


def test_all_golden_scenarios_convert_to_langsmith_examples() -> None:
    examples = golden_scenarios_to_langsmith_examples()

    assert len(examples) == len(load_golden_scenarios())
    assert all("business_expectation" in example["outputs"] for example in examples)
    assert all("expected" in example["outputs"] for example in examples)


def test_langsmith_export_requires_api_key(monkeypatch) -> None:
    monkeypatch.setattr("evals.langsmith_export.settings.LANGSMITH_API_KEY", None)

    with pytest.raises(LangSmithEvaluationConfigError, match="LANGSMITH_API_KEY"):
        require_langsmith_evaluation_config()


def test_langsmith_target_runs_local_deterministic_scenario() -> None:
    output = run_scenario_for_langsmith({"scenario_id": "cracked_screen_blocked"})

    assert output["scenario_id"] == "cracked_screen_blocked"
    assert output["passed"] is True
    assert output["outcome"] == "blocked"
    assert output["intake_result_summary"]["can_start_workflow"] is True
    assert output["workflow_result_summary"]["guardrail_decision"] == "block"
    assert output["failure_reasons"] == []


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
