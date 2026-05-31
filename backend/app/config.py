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
