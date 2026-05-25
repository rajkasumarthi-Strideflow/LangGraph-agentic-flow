from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite:///./warrantywise.db"

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
