from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.audit.store import clear_audit_events
from app.config import settings
from app.intake.router import route_customer_message
from app.workflow.graph import run_warranty_workflow
from app.workflow.state import WarrantyWorkflowState

from evals.assertions import assert_eval_result

SCENARIOS_PATH = Path(__file__).with_name("golden_scenarios.json")


@contextmanager
def _deterministic_eval_mode():
    original_api_key = settings.OPENAI_API_KEY
    original_model = settings.OPENAI_MODEL
    try:
        settings.OPENAI_API_KEY = None
        settings.OPENAI_MODEL = None
        yield
    finally:
        settings.OPENAI_API_KEY = original_api_key
        settings.OPENAI_MODEL = original_model


def load_golden_scenarios(path: Path = SCENARIOS_PATH) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as file:
        scenarios = json.load(file)
    if not isinstance(scenarios, list):
        raise ValueError("Golden scenarios file must contain a list.")
    return scenarios


def _initial_state(
    *,
    scenario_id: str,
    customer_request: str,
    customer_id: str,
    order_id: str,
) -> WarrantyWorkflowState:
    return {
        "workflow_id": f"eval_{scenario_id}_{uuid4().hex}",
        "correlation_id": f"corr_eval_{uuid4().hex}",
        "customer_request": customer_request,
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


def _scenario_message(scenario: dict[str, Any]) -> str:
    scenario_input = scenario["input"]
    if isinstance(scenario_input, str):
        return scenario_input
    if isinstance(scenario_input, dict) and isinstance(scenario_input.get("message"), str):
        return scenario_input["message"]
    raise ValueError(f"Scenario {scenario.get('id', 'unknown')} input.message is required.")


def _run_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    message = _scenario_message(scenario)
    intake_result = route_customer_message(message)
    workflow_result: dict[str, Any] | None = None

    should_start = scenario["expected"].get("workflow_should_start", False)
    if should_start:
        if not intake_result.get("can_start_workflow"):
            raise AssertionError("scenario expected workflow start, but intake was not ready")
        workflow_result = dict(
            run_warranty_workflow(
                _initial_state(
                    scenario_id=scenario["id"],
                    customer_request=message,
                    customer_id=intake_result["customer_id"],
                    order_id=intake_result["order_id"],
                )
            )
        )

    assert_eval_result(scenario, intake_result, workflow_result)
    return {
        "scenario_id": scenario["id"],
        "passed": True,
        "intake": intake_result,
        "workflow": workflow_result,
    }


def run_golden_scenario_evaluations() -> dict[str, Any]:
    scenarios = load_golden_scenarios()
    clear_audit_events()

    failures: list[dict[str, str]] = []
    scenario_results: list[dict[str, Any]] = []

    with _deterministic_eval_mode():
        for scenario in scenarios:
            try:
                scenario_results.append(_run_scenario(scenario))
            except AssertionError as exc:
                failures.append(
                    {
                        "scenario_id": scenario.get("id", "unknown"),
                        "error": str(exc),
                    }
                )
                scenario_results.append(
                    {
                        "scenario_id": scenario.get("id", "unknown"),
                        "passed": False,
                        "error": str(exc),
                    }
                )

    return {
        "total_scenarios": len(scenarios),
        "passed": len(scenarios) - len(failures),
        "failed": len(failures),
        "failures": failures,
        "scenario_results": scenario_results,
    }


def main() -> None:
    summary = run_golden_scenario_evaluations()
    print(json.dumps(summary, indent=2, sort_keys=True))
    if summary["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
