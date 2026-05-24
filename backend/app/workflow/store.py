from typing import Any


WORKFLOW_RESULTS: dict[str, dict[str, Any]] = {}


def save_workflow_result(workflow_id: str, state: dict[str, Any]) -> dict[str, Any]:
    WORKFLOW_RESULTS[workflow_id] = state
    return state


def get_workflow_result(workflow_id: str) -> dict[str, Any] | None:
    return WORKFLOW_RESULTS.get(workflow_id)


def clear_workflow_results() -> None:
    WORKFLOW_RESULTS.clear()
