"""
Application settings and configuration management.

This module provides centralized configuration management using Pydantic Settings,
which automatically loads configuration from environment variables, .env files,
and provides validation and type conversion.
"""

from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with automatic environment variable loading."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Application settings
    app_name: str = "AI Career Mentor Chatbot"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    allowed_hosts: str = "localhost,127.0.0.1"

    # Azure OpenAI Configuration
    azure_openai_endpoint: str = "https://your-openai.openai.azure.com/"
    azure_openai_key: str = "your-azure-openai-key"
    azure_openai_api_version: str = "2023-12-01-preview"
    azure_openai_deployment_name: str = "gpt-4"

    # Azure Cognitive Search Configuration
    azure_search_endpoint: str = "https://your-search.search.windows.net"
    azure_search_key: str = "your-azure-search-key"
    azure_search_index_name: str = "career-knowledge"

    # RAG Configuration
    rag_max_search_results: int = 5
    rag_min_confidence_score: float = 0.7
    rag_enable_by_default: bool = True

    # Embedding Configuration
    azure_openai_embedding_deployment: str = "text-embedding-ada-002"
    embedding_dimensions: int = 1536

    # Azure Cosmos DB Configuration
    azure_cosmos_endpoint: str = "https://your-cosmos.documents.azure.com:443/"
    azure_cosmos_key: str = "your-azure-cosmos-key"
    azure_cosmos_database_name: str = "chatbot"
    azure_cosmos_container_name: str = "conversations"

    # Azure Key Vault (optional for production)
    azure_key_vault_url: Optional[str] = None

    # Application Insights (optional for production)
    azure_application_insights_connection_string: Optional[str] = None

    # Chat Configuration
    max_conversation_history: int = 20
    default_temperature: float = 0.7
    max_tokens: int = 1000

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour

    @property
    def allowed_hosts_list(self) -> list[str]:
        """Parse comma-separated allowed hosts string into list."""
        return [host.strip() for host in self.allowed_hosts.split(",")]

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    @field_validator("default_temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is between 0 and 2."""
        if not 0 <= v <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        return v

    @field_validator("rag_min_confidence_score")
    @classmethod
    def validate_rag_confidence(cls, v: float) -> float:
        """Validate RAG confidence score is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("RAG confidence score must be between 0 and 1")
        return v

    @field_validator("rag_max_search_results")
    @classmethod
    def validate_rag_max_results(cls, v: int) -> int:
        """Validate RAG max search results is reasonable."""
        if not 1 <= v <= 20:
            raise ValueError("RAG max search results must be between 1 and 20")
        return v


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings instance.

    This function creates a new Settings instance each time it's called,
    allowing for dynamic configuration updates by reloading or
    changing environment variables during runtime.

    Returns:
        Settings: The application settings instance
    """
    return Settings()


# Convenience function for getting settings in dependency injection
def get_settings_dependency() -> Settings:
    """FastAPI dependency for getting settings."""
    return get_settings()
