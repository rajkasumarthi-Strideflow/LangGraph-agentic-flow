from typing import Any

from app.observability.langsmith_tracing import traceable_if_enabled


def _read_usage_value(usage: Any, key: str) -> int | None:
    if usage is None:
        return None
    if isinstance(usage, dict):
        value = usage.get(key)
    else:
        value = getattr(usage, key, None)
    return int(value) if isinstance(value, int) else None


def _read_cached_tokens(usage: Any) -> int | None:
    if usage is None:
        return None

    details = None
    if isinstance(usage, dict):
        details = usage.get("input_tokens_details") or usage.get("input_token_details")
    else:
        details = getattr(usage, "input_tokens_details", None) or getattr(
            usage,
            "input_token_details",
            None,
        )

    if isinstance(details, dict):
        value = details.get("cached_tokens")
    else:
        value = getattr(details, "cached_tokens", None)
    return int(value) if isinstance(value, int) else None


@traceable_if_enabled(name="extract_llm_usage")
def extract_usage(response: Any) -> dict[str, int | None]:
    usage = getattr(response, "usage", None)
    return {
        "input_tokens": _read_usage_value(usage, "input_tokens"),
        "output_tokens": _read_usage_value(usage, "output_tokens"),
        "total_tokens": _read_usage_value(usage, "total_tokens"),
        "cached_tokens": _read_cached_tokens(usage),
    }
