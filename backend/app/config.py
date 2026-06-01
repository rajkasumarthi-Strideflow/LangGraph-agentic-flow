from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite:///./warrantywise.db"
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str | None = None
    LLM_RESPONSE_DRAFTING_ENABLED: bool = True
    LANGSMITH_TRACING: bool = False
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_PROJECT: str = "decisiontrace-phase2"
    LANGSMITH_ENDPOINT: str | None = None
    LANGSMITH_EVALUATION_ENABLED: bool = False
    LANGSMITH_EVALUATION_DATASET: str = "decisiontrace-phase2-golden-scenarios"
    LANGSMITH_EVALUATION_EXPERIMENT_PREFIX: str = "decisiontrace-phase2"

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace(
                "postgresql://",
                "postgresql+psycopg://",
                1,
            )
        return self.DATABASE_URL


settings = Settings()
