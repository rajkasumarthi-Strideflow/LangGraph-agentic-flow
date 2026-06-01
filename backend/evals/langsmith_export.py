from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from app.config import settings

from evals.runner import (
    _deterministic_eval_mode,
    _run_scenario,
    load_golden_scenarios,
)


class LangSmithEvaluationConfigError(RuntimeError):
    """Raised when optional LangSmith evaluation is invoked without config."""


def require_langsmith_evaluation_config() -> None:
    if not settings.LANGSMITH_API_KEY:
        raise LangSmithEvaluationConfigError(
            "LANGSMITH_API_KEY is required to sync datasets or run LangSmith "
            "experiments. Local deterministic pytest evaluations do not require "
            "LangSmith configuration."
        )


def scenario_to_langsmith_example(scenario: dict[str, Any]) -> dict[str, Any]:
    scenario_input = scenario["input"]
    message = scenario_input["message"] if isinstance(scenario_input, dict) else scenario_input
    return {
        "inputs": {
            "scenario_id": scenario["id"],
            "message": message,
            "input": scenario_input,
        },
        "outputs": {
            "business_scenario": scenario["business_scenario"],
            "business_expectation": scenario["business_expectation"],
            "control_model_expectation": scenario["control_model_expectation"],
            "expected": scenario["expected"],
        },
        "metadata": {
            "scenario_id": scenario["id"],
            "scenario_name": scenario["name"],
            "evaluation_type": "deterministic_control_model",
        },
    }


def golden_scenarios_to_langsmith_examples() -> list[dict[str, Any]]:
    return [scenario_to_langsmith_example(scenario) for scenario in load_golden_scenarios()]


def _langsmith_client():
    require_langsmith_evaluation_config()
    try:
        from langsmith import Client
    except Exception as exc:
        raise LangSmithEvaluationConfigError(
            "The langsmith package is required for optional evaluation export."
        ) from exc

    client_kwargs: dict[str, Any] = {"api_key": settings.LANGSMITH_API_KEY}
    if settings.LANGSMITH_ENDPOINT:
        client_kwargs["api_url"] = settings.LANGSMITH_ENDPOINT
    return Client(**client_kwargs)


def _get_or_create_dataset(client: Any, dataset_name: str) -> Any:
    datasets = list(client.list_datasets(dataset_name=dataset_name, limit=1))
    if datasets:
        return datasets[0]
    return client.create_dataset(
        dataset_name,
        description=(
            "DecisionTrace AI Phase 2 golden scenarios for deterministic "
            "control-model evaluation."
        ),
        metadata={
            "project": settings.LANGSMITH_PROJECT,
            "source": "backend/evals/golden_scenarios.json",
        },
    )


def sync_golden_scenarios_to_langsmith(
    *,
    dataset_name: str | None = None,
) -> dict[str, Any]:
    client = _langsmith_client()
    target_dataset_name = dataset_name or settings.LANGSMITH_EVALUATION_DATASET
    dataset = _get_or_create_dataset(client, target_dataset_name)

    existing_examples = list(client.list_examples(dataset_id=dataset.id))
    existing_scenario_ids = {
        (example.metadata or {}).get("scenario_id")
        for example in existing_examples
    }

    created = 0
    skipped = 0
    for example in golden_scenarios_to_langsmith_examples():
        scenario_id = example["metadata"]["scenario_id"]
        if scenario_id in existing_scenario_ids:
            skipped += 1
            continue
        client.create_example(
            dataset_id=dataset.id,
            inputs=example["inputs"],
            outputs=example["outputs"],
            metadata=example["metadata"],
        )
        created += 1

    return {
        "dataset_name": target_dataset_name,
        "dataset_id": str(dataset.id),
        "created_examples": created,
        "skipped_existing_examples": skipped,
    }


def _find_scenario(scenario_id: str) -> dict[str, Any]:
    for scenario in load_golden_scenarios():
        if scenario["id"] == scenario_id:
            return scenario
    raise ValueError(f"Unknown golden scenario: {scenario_id}")


def _summarize_intake(intake: dict[str, Any] | None) -> dict[str, Any] | None:
    if intake is None:
        return None
    return {
        "intent": intake.get("intent"),
        "requires_clarification": intake.get("requires_clarification"),
        "missing_fields": intake.get("missing_fields"),
        "invalid_fields": intake.get("invalid_fields"),
        "can_start_workflow": intake.get("can_start_workflow"),
        "routed_workflow": intake.get("routed_workflow"),
    }


def _summarize_workflow(workflow: dict[str, Any] | None) -> dict[str, Any] | None:
    if workflow is None:
        return None
    return {
        "workflow_id": workflow.get("workflow_id"),
        "correlation_id": workflow.get("correlation_id"),
        "workflow_status": workflow.get("workflow_status"),
        "identity_verified": workflow.get("identity_verified"),
        "eligibility_status": workflow.get("eligibility_status"),
        "guardrail_decision": workflow.get("guardrail_decision"),
        "replacement_request_id": workflow.get("replacement_request_id"),
        "escalation_id": workflow.get("escalation_id"),
        "final_response_source": workflow.get("final_response_source"),
    }


def _outcome_from_result(result: dict[str, Any]) -> str:
    workflow = result.get("workflow")
    intake = result.get("intake") or {}
    if workflow:
        if workflow.get("replacement_request_id"):
            return "allowed_action"
        if workflow.get("escalation_id"):
            return "escalated"
        if workflow.get("guardrail_decision") == "block":
            return "blocked"
        return "completed_no_action"
    if intake.get("invalid_fields"):
        return "invalid_input"
    if intake.get("requires_clarification"):
        return "clarification_required"
    return "unknown"


def run_scenario_for_langsmith(inputs: dict[str, Any]) -> dict[str, Any]:
    scenario_id = inputs["scenario_id"]
    scenario = _find_scenario(scenario_id)
    try:
        with _deterministic_eval_mode():
            result = _run_scenario(scenario)
    except AssertionError as exc:
        return {
            "scenario_id": scenario_id,
            "passed": False,
            "intake_result_summary": None,
            "workflow_result_summary": None,
            "outcome": "failed",
            "correlation_id": None,
            "failure_reasons": [str(exc)],
        }

    workflow_summary = _summarize_workflow(result.get("workflow"))
    return {
        "scenario_id": scenario_id,
        "passed": True,
        "intake_result_summary": _summarize_intake(result.get("intake")),
        "workflow_result_summary": workflow_summary,
        "outcome": _outcome_from_result(result),
        "correlation_id": workflow_summary.get("correlation_id") if workflow_summary else None,
        "failure_reasons": [],
    }


def control_model_passed(outputs: dict[str, Any] | None = None, **_: Any) -> dict[str, Any]:
    return {
        "key": "control_model_passed",
        "score": bool((outputs or {}).get("passed")),
    }


def expected_outcome_matched(outputs: dict[str, Any] | None = None, **_: Any) -> dict[str, Any]:
    return {
        "key": "expected_outcome_matched",
        "score": bool((outputs or {}).get("passed")),
    }


def no_overpromise(outputs: dict[str, Any] | None = None, **_: Any) -> dict[str, Any]:
    failure_reasons = (outputs or {}).get("failure_reasons") or []
    return {
        "key": "no_overpromise",
        "score": not any("claim" in reason.lower() for reason in failure_reasons),
    }


def run_langsmith_experiment(
    *,
    dataset_name: str | None = None,
    experiment_prefix: str | None = None,
) -> dict[str, Any]:
    client = _langsmith_client()
    target_dataset_name = dataset_name or settings.LANGSMITH_EVALUATION_DATASET
    target_experiment_prefix = (
        experiment_prefix or settings.LANGSMITH_EVALUATION_EXPERIMENT_PREFIX
    )
    results = client.evaluate(
        run_scenario_for_langsmith,
        data=target_dataset_name,
        evaluators=[
            control_model_passed,
            expected_outcome_matched,
            no_overpromise,
        ],
        experiment_prefix=target_experiment_prefix,
        metadata={
            "evaluation_type": "deterministic_control_model",
            "source": "backend/evals/langsmith_export.py",
        },
    )
    return {
        "dataset_name": target_dataset_name,
        "experiment_prefix": target_experiment_prefix,
        "results": str(results),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Optional LangSmith integration for DecisionTrace golden scenarios."
    )
    parser.add_argument("--sync-dataset", action="store_true")
    parser.add_argument("--run-experiment", action="store_true")
    args = parser.parse_args()

    if not args.sync_dataset and not args.run_experiment:
        parser.error("Specify --sync-dataset and/or --run-experiment.")

    output: dict[str, Any] = {}
    try:
        if args.sync_dataset:
            output["sync_dataset"] = sync_golden_scenarios_to_langsmith()
        if args.run_experiment:
            output["run_experiment"] = run_langsmith_experiment()
    except LangSmithEvaluationConfigError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from None
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
