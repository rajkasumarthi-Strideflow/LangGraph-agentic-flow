from fastapi.testclient import TestClient

from app.config import Settings, settings
from app.main import app


def test_app_imports_successfully() -> None:
    assert app.title == "WarrantyWise Agentic Support Platform"


def test_health_still_works_for_deployment() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_frontend_root_still_serves_for_deployment() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "DecisionTrace AI" in response.text


def test_database_url_default_is_sqlite() -> None:
    local_settings = Settings(_env_file=None)

    assert local_settings.DATABASE_URL == "sqlite:///./warrantywise.db"
    assert local_settings.sqlalchemy_database_url == "sqlite:///./warrantywise.db"
    assert settings.sqlalchemy_database_url.startswith("sqlite")


def test_postgres_url_normalization_for_railway() -> None:
    local_settings = Settings(
        DATABASE_URL="postgresql://user:password@host:5432/dbname",
    )

    assert (
        local_settings.sqlalchemy_database_url
        == "postgresql+psycopg://user:password@host:5432/dbname"
    )
