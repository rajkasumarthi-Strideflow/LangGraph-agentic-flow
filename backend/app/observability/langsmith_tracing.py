import os
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from app.config import settings

F = TypeVar("F", bound=Callable[..., Any])


def is_langsmith_enabled() -> bool:
    return bool(settings.LANGSMITH_TRACING and settings.LANGSMITH_API_KEY)


def get_langsmith_project() -> str:
    return settings.LANGSMITH_PROJECT or "decisiontrace-phase2"


def _configure_langsmith_environment() -> None:
    if not is_langsmith_enabled():
        return

    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGSMITH_API_KEY", settings.LANGSMITH_API_KEY or "")
    os.environ.setdefault("LANGCHAIN_API_KEY", settings.LANGSMITH_API_KEY or "")
    os.environ.setdefault("LANGSMITH_PROJECT", get_langsmith_project())
    os.environ.setdefault("LANGCHAIN_PROJECT", get_langsmith_project())
    if settings.LANGSMITH_ENDPOINT:
        os.environ.setdefault("LANGSMITH_ENDPOINT", settings.LANGSMITH_ENDPOINT)
        os.environ.setdefault("LANGCHAIN_ENDPOINT", settings.LANGSMITH_ENDPOINT)


def get_langsmith_status() -> dict[str, Any]:
    if not settings.LANGSMITH_TRACING:
        tracing_status = "disabled"
    elif not settings.LANGSMITH_API_KEY:
        tracing_status = "not_configured"
    else:
        tracing_status = "enabled"

    return {
        "provider": "langsmith",
        "tracing_status": tracing_status,
        "project": get_langsmith_project(),
        "trace_url": None,
        "trace_url_supported": False,
    }


def traceable_if_enabled(
    *,
    name: str | None = None,
    run_type: str = "chain",
) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        if not is_langsmith_enabled():
            return func

        _configure_langsmith_environment()
        try:
            from langsmith import traceable
        except Exception:
            return func

        try:
            traced = traceable(name=name or func.__name__, run_type=run_type)(func)
            trace_name = name or func.__name__

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                metadata = _metadata_from_call(
                    component=trace_name,
                    args=args,
                    kwargs=kwargs,
                )
                try:
                    return traced(
                        *args,
                        **kwargs,
                        **with_langsmith_metadata(metadata),
                    )
                except TypeError:
                    return traced(*args, **kwargs)

            return cast(F, wrapper)
        except Exception:
            return func

    return decorator


def _extract_metadata_value(source: Any, key: str) -> Any:
    if source is None:
        return None
    if isinstance(source, dict):
        return source.get(key)
    return getattr(source, key, None)


def _metadata_from_call(
    *,
    component: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    metadata: dict[str, Any] = {"component": component}
    for source in [*args, *kwargs.values()]:
        for key in ["correlation_id", "intake_session_id", "workflow_id"]:
            metadata.setdefault(key, _extract_metadata_value(source, key))
        if _extract_metadata_value(source, "eligibility_status"):
            metadata.setdefault(
                "eligibility_status",
                _extract_metadata_value(source, "eligibility_status"),
            )
        if _extract_metadata_value(source, "guardrail_decision"):
            metadata.setdefault(
                "guardrail_decision",
                _extract_metadata_value(source, "guardrail_decision"),
            )
        if _extract_metadata_value(source, "routing_status"):
            metadata.setdefault(
                "routing_status",
                _extract_metadata_value(source, "routing_status"),
            )

    return {key: value for key, value in metadata.items() if value is not None}


def with_langsmith_metadata(metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    if not is_langsmith_enabled():
        return {}
    safe_metadata = {
        key: value
        for key, value in (metadata or {}).items()
        if value is not None
    }
    return {"langsmith_extra": {"metadata": safe_metadata}}


def safe_trace_wrapper(
    func: Callable[..., Any],
    *,
    name: str,
) -> Callable[..., Any]:
    traced = traceable_if_enabled(name=name)(func)

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return traced(*args, **kwargs)

    return wrapper
