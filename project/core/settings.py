from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database connection string
    DB_CONNECTION: str

    # AI API Keys
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str

    # Environment setting (e.g., "dev", "prod")
    ENVIRONMENT: Literal["dev", "prod"] = "dev"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
