import pytest

from app.config import settings


@pytest.fixture(autouse=True)
def disable_openai_credentials_for_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)
    monkeypatch.setattr(settings, "OPENAI_MODEL", None)
    monkeypatch.setattr(settings, "LLM_RESPONSE_DRAFTING_ENABLED", True)
