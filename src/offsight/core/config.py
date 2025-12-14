"""
Configuration settings for OffSight.

Uses Pydantic settings with support for environment variables and .env files.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database configuration
    database_url: str = Field(
        default="postgresql+psycopg2://user:pass@localhost:5432/offsight",
        alias="DATABASE_URL",
        description="PostgreSQL database connection URL",
    )

    # Ollama configuration
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",
        description="Base URL for Ollama API",
    )
    ollama_model: str = Field(
        default="llama3.1",
        alias="OLLAMA_MODEL",
        description="Ollama model name to use for AI analysis",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: The application settings instance.
    """
    return Settings()

