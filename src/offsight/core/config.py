"""
Configuration settings for OffSight.

Uses Pydantic settings with support for environment variables and .env files.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    
    This class uses Pydantic Settings to load configuration from:
    1. Environment variables (highest priority)
    2. .env file in project root
    3. Default values (lowest priority)
    
    All settings can be overridden via environment variables using the
    aliases specified in Field() definitions.
    
    Attributes:
        database_url: PostgreSQL connection string
        ollama_base_url: Base URL for Ollama API
        ollama_model: Ollama model name to use
        demo_source_url: GitHub Pages URL for demo regulation source
    """

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

    # Demo configuration
    demo_source_url: str = Field(
        default="https://<your-username>.github.io/offsight-demo-regulation/",
        alias="DEMO_SOURCE_URL",
        description="GitHub Pages URL used as the primary controlled demo source",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",  # Ignore extra fields from .env file
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: The application settings instance.
    """
    return Settings()

