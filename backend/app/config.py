"""Application configuration, loaded from environment / `.env`.

A single typed `Settings` object is the source of truth for every tunable.
It is cached so the same instance is shared across the process.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ProviderName = Literal["mock", "anthropic", "openai"]


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Core ---
    app_env: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"])

    # --- Database ---
    database_url: str = "sqlite+aiosqlite:///./aiteam.db"

    # --- LLM provider ---
    llm_provider: ProviderName = "mock"
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-6"
    openai_model: str = "gpt-4o"

    # --- Orchestration ---
    max_iterations: int = 2
    agent_max_retries: int = 2
    mock_latency_seconds: float = 0.6

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, value: object) -> object:
        """Allow CORS origins as a comma-separated string in the environment."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    def default_model_for(self, provider: ProviderName) -> str:
        """Return the configured model name for a given provider."""
        return {
            "mock": "mock-architect-1",
            "anthropic": self.anthropic_model,
            "openai": self.openai_model,
        }[provider]


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide cached settings instance."""
    return Settings()


settings = get_settings()
