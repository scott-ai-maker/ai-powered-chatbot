"""
Application settings and configuration management.

This module provides centralized configuration management using Pydantic Settings,
which automatically loads configuration from environment variables, .env files,
and provides validation and type conversion.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with automatic environment variable loading."""

    # Application settings
    app_name: str = Field(default="AI Career Mentor Chatbot", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    allowed_hosts: str = Field(default="localhost,127.0.0.1", env="ALLOWED_HOSTS")

    # Azure OpenAI Configuration
    azure_openai_endpoint: str = Field(..., env="AZURE_OPENAI_ENDPOINT")
    azure_openai_key: str = Field(..., env="AZURE_OPENAI_KEY")
    azure_openai_api_version: str = Field(
        default="2023-12-01-preview", env="AZURE_OPENAI_API_VERSION"
    )
    azure_openai_deployment_name: str = Field(
        default="gpt-4", env="AZURE_OPENAI_DEPLOYMENT_NAME"
    )

    # Azure Cognitive Search Configuration
    azure_search_endpoint: str = Field(..., env="AZURE_SEARCH_ENDPOINT")
    azure_search_key: str = Field(..., env="AZURE_SEARCH_KEY")
    azure_search_index_name: str = Field(
        default="career-knowledge", env="AZURE_SEARCH_INDEX_NAME"
    )

    # RAG Configuration
    rag_max_search_results: int = Field(default=5, env="RAG_MAX_SEARCH_RESULTS")
    rag_min_confidence_score: float = Field(default=0.7, env="RAG_MIN_CONFIDENCE_SCORE")
    rag_enable_by_default: bool = Field(default=True, env="RAG_ENABLE_BY_DEFAULT")

    # Embedding Configuration
    azure_openai_embedding_deployment: str = Field(
        default="text-embedding-ada-002", env="AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
    )
    embedding_dimensions: int = Field(default=1536, env="EMBEDDING_DIMENSIONS")

    # Azure Cosmos DB Configuration
    azure_cosmos_endpoint: str = Field(..., env="AZURE_COSMOS_ENDPOINT")
    azure_cosmos_key: str = Field(..., env="AZURE_COSMOS_KEY")
    azure_cosmos_database_name: str = Field(
        default="chatbot", env="AZURE_COSMOS_DATABASE_NAME"
    )
    azure_cosmos_container_name: str = Field(
        default="conversations", env="AZURE_COSMOS_CONTAINER_NAME"
    )

    # Azure Key Vault (optional for production)
    azure_key_vault_url: Optional[str] = Field(default=None, env="AZURE_KEY_VAULT_URL")

    # Application Insights (optional for production)
    azure_application_insights_connection_string: Optional[str] = Field(
        default=None, env="AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING"
    )

    # Chat Configuration
    max_conversation_history: int = Field(default=20, env="MAX_CONVERSATION_HISTORY")
    default_temperature: float = Field(default=0.7, env="DEFAULT_TEMPERATURE")
    max_tokens: int = Field(default=1000, env="MAX_TOKENS")

    # Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, env="RATE_LIMIT_WINDOW")  # 1 hour

    @property
    def allowed_hosts_list(self) -> list[str]:
        """Parse comma-separated allowed hosts string into list."""
        return [host.strip() for host in self.allowed_hosts.split(",")]

    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level is one of the standard levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    @validator("default_temperature")
    def validate_temperature(cls, v):
        """Validate temperature is between 0 and 2."""
        if not 0 <= v <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        return v

    @validator("rag_min_confidence_score")
    def validate_rag_confidence(cls, v):
        """Validate RAG confidence score is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("RAG confidence score must be between 0 and 1")
        return v

    @validator("rag_max_search_results")
    def validate_rag_max_results(cls, v):
        """Validate RAG max search results is reasonable."""
        if not 1 <= v <= 20:
            raise ValueError("RAG max search results must be between 1 and 20")
        return v

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings with caching.

    Using lru_cache ensures we only load the settings once during the
    application lifecycle, which is efficient and prevents issues with
    changing environment variables during runtime.

    Returns:
        Settings: The application settings instance
    """
    return Settings()


# Convenience function for getting settings in dependency injection
def get_settings_dependency() -> Settings:
    """FastAPI dependency for getting settings."""
    return get_settings()
