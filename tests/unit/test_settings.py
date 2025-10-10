"""
Unit tests for configuration and settings.

These tests demonstrate validation of configuration management,
environment variable handling, and settings validation patterns
that are crucial for production applications.
"""

import pytest
import os
from unittest.mock import patch
from pydantic import ValidationError

from src.config.settings import Settings


class TestSettings:
    """Test the Settings configuration class."""

    def test_default_settings_creation(self):
        """Test creating settings with default values."""
        # Mock environment variables for required fields
        with patch.dict(
            os.environ,
            {
                "AZURE_OPENAI_API_KEY": "test_key",
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
                "AZURE_OPENAI_DEPLOYMENT_NAME": "test-gpt-4",
            },
        ):
            settings = Settings()

            # Check required fields
            assert settings.azure_openai_api_key == "test_key"
            assert settings.azure_openai_endpoint == "https://test.openai.azure.com/"
            assert settings.azure_openai_deployment_name == "test-gpt-4"

            # Check defaults
            assert settings.azure_openai_api_version == "2024-02-15-preview"
            assert settings.default_temperature == 0.7
            assert settings.default_max_tokens == 4000
            assert settings.log_level == "INFO"
            assert settings.debug is False

    def test_settings_from_environment_variables(self):
        """Test loading settings from environment variables."""
        env_vars = {
            "AZURE_OPENAI_API_KEY": "env_test_key",
            "AZURE_OPENAI_ENDPOINT": "https://env-test.openai.azure.com/",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "env-gpt-4",
            "AZURE_OPENAI_API_VERSION": "2024-03-01-preview",
            "DEFAULT_TEMPERATURE": "0.8",
            "DEFAULT_MAX_TOKENS": "3000",
            "LOG_LEVEL": "DEBUG",
            "DEBUG": "true",
        }

        with patch.dict(os.environ, env_vars):
            settings = Settings()

            # Verify all environment variables were loaded
            assert settings.azure_openai_api_key == "env_test_key"
            assert (
                settings.azure_openai_endpoint == "https://env-test.openai.azure.com/"
            )
            assert settings.azure_openai_deployment_name == "env-gpt-4"
            assert settings.azure_openai_api_version == "2024-03-01-preview"
            assert settings.default_temperature == 0.8
            assert settings.default_max_tokens == 3000
            assert settings.log_level == "DEBUG"
            assert settings.debug is True

    def test_missing_required_api_key(self):
        """Test that missing API key raises validation error."""
        with patch.dict(
            os.environ,
            {
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
                "AZURE_OPENAI_DEPLOYMENT_NAME": "test-gpt-4",
            },
            clear=True,
        ):
            with pytest.raises(ValidationError) as exc_info:
                Settings()

            # Check that the API key field is mentioned in the error
            assert "azure_openai_api_key" in str(exc_info.value)

    def test_missing_required_endpoint(self):
        """Test that missing endpoint raises validation error."""
        with patch.dict(
            os.environ,
            {
                "AZURE_OPENAI_API_KEY": "test_key",
                "AZURE_OPENAI_DEPLOYMENT_NAME": "test-gpt-4",
            },
            clear=True,
        ):
            with pytest.raises(ValidationError) as exc_info:
                Settings()

            assert "azure_openai_endpoint" in str(exc_info.value)

    def test_missing_required_deployment_name(self):
        """Test that missing deployment name raises validation error."""
        with patch.dict(
            os.environ,
            {
                "AZURE_OPENAI_API_KEY": "test_key",
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            },
            clear=True,
        ):
            with pytest.raises(ValidationError) as exc_info:
                Settings()

            assert "azure_openai_deployment_name" in str(exc_info.value)

    def test_temperature_validation(self):
        """Test temperature parameter validation."""
        base_env = {
            "AZURE_OPENAI_API_KEY": "test_key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "test-gpt-4",
        }

        # Valid temperatures
        for temp in ["0.0", "0.5", "1.0", "2.0"]:
            with patch.dict(os.environ, {**base_env, "DEFAULT_TEMPERATURE": temp}):
                settings = Settings()
                assert settings.default_temperature == float(temp)

        # Invalid temperatures
        for invalid_temp in ["-0.1", "2.1", "5.0", "invalid"]:
            with patch.dict(
                os.environ, {**base_env, "DEFAULT_TEMPERATURE": invalid_temp}
            ):
                with pytest.raises(ValidationError):
                    Settings()

    def test_max_tokens_validation(self):
        """Test max_tokens parameter validation."""
        base_env = {
            "AZURE_OPENAI_API_KEY": "test_key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "test-gpt-4",
        }

        # Valid max_tokens
        for tokens in ["100", "1000", "4000", "8000"]:
            with patch.dict(os.environ, {**base_env, "DEFAULT_MAX_TOKENS": tokens}):
                settings = Settings()
                assert settings.default_max_tokens == int(tokens)

        # Invalid max_tokens
        for invalid_tokens in ["0", "-100", "invalid"]:
            with patch.dict(
                os.environ, {**base_env, "DEFAULT_MAX_TOKENS": invalid_tokens}
            ):
                with pytest.raises(ValidationError):
                    Settings()

    def test_log_level_validation(self):
        """Test log level validation."""
        base_env = {
            "AZURE_OPENAI_API_KEY": "test_key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "test-gpt-4",
        }

        # Valid log levels
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            with patch.dict(os.environ, {**base_env, "LOG_LEVEL": level}):
                settings = Settings()
                assert settings.log_level == level

        # Case insensitive
        with patch.dict(os.environ, {**base_env, "LOG_LEVEL": "debug"}):
            settings = Settings()
            assert settings.log_level == "DEBUG"

        # Invalid log level
        with patch.dict(os.environ, {**base_env, "LOG_LEVEL": "INVALID"}):
            with pytest.raises(ValidationError):
                Settings()

    def test_debug_flag_parsing(self):
        """Test debug flag parsing from various string values."""
        base_env = {
            "AZURE_OPENAI_API_KEY": "test_key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "test-gpt-4",
        }

        # Truthy values
        for true_value in ["true", "True", "TRUE", "1", "yes", "on"]:
            with patch.dict(os.environ, {**base_env, "DEBUG": true_value}):
                settings = Settings()
                assert settings.debug is True

        # Falsy values
        for false_value in ["false", "False", "FALSE", "0", "no", "off", ""]:
            with patch.dict(os.environ, {**base_env, "DEBUG": false_value}):
                settings = Settings()
                assert settings.debug is False

    def test_endpoint_url_validation(self):
        """Test Azure OpenAI endpoint URL validation."""
        base_env = {
            "AZURE_OPENAI_API_KEY": "test_key",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "test-gpt-4",
        }

        # Valid URLs
        valid_urls = [
            "https://test.openai.azure.com/",
            "https://test.openai.azure.com",
            "https://my-resource.openai.azure.com/",
            "https://my-resource-123.openai.azure.com/",
        ]

        for url in valid_urls:
            with patch.dict(os.environ, {**base_env, "AZURE_OPENAI_ENDPOINT": url}):
                settings = Settings()
                assert settings.azure_openai_endpoint == url

        # Invalid URLs
        invalid_urls = [
            "http://test.openai.azure.com/",  # HTTP instead of HTTPS
            "not-a-url",
            "ftp://test.openai.azure.com/",
            "",
        ]

        for invalid_url in invalid_urls:
            with patch.dict(
                os.environ, {**base_env, "AZURE_OPENAI_ENDPOINT": invalid_url}
            ):
                with pytest.raises(ValidationError):
                    Settings()

    def test_azure_search_configuration(self):
        """Test Azure Cognitive Search configuration."""
        base_env = {
            "AZURE_OPENAI_API_KEY": "test_key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "test-gpt-4",
        }

        # Without Azure Search
        with patch.dict(os.environ, base_env):
            settings = Settings()
            assert settings.azure_search_endpoint is None
            assert settings.azure_search_api_key is None
            assert settings.azure_search_index_name is None

        # With complete Azure Search configuration
        search_env = {
            **base_env,
            "AZURE_SEARCH_ENDPOINT": "https://test-search.search.windows.net",
            "AZURE_SEARCH_API_KEY": "search_key",
            "AZURE_SEARCH_INDEX_NAME": "test-index",
        }

        with patch.dict(os.environ, search_env):
            settings = Settings()
            assert (
                settings.azure_search_endpoint
                == "https://test-search.search.windows.net"
            )
            assert settings.azure_search_api_key == "search_key"
            assert settings.azure_search_index_name == "test-index"

    def test_cosmos_db_configuration(self):
        """Test Azure Cosmos DB configuration."""
        base_env = {
            "AZURE_OPENAI_API_KEY": "test_key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "test-gpt-4",
        }

        # Without Cosmos DB
        with patch.dict(os.environ, base_env):
            settings = Settings()
            assert settings.cosmos_db_endpoint is None
            assert settings.cosmos_db_key is None
            assert settings.cosmos_db_database_name is None
            assert settings.cosmos_db_container_name is None

        # With complete Cosmos DB configuration
        cosmos_env = {
            **base_env,
            "COSMOS_DB_ENDPOINT": "https://test-cosmos.documents.azure.com:443/",
            "COSMOS_DB_KEY": "cosmos_key",
            "COSMOS_DB_DATABASE_NAME": "chatbot",
            "COSMOS_DB_CONTAINER_NAME": "conversations",
        }

        with patch.dict(os.environ, cosmos_env):
            settings = Settings()
            assert (
                settings.cosmos_db_endpoint
                == "https://test-cosmos.documents.azure.com:443/"
            )
            assert settings.cosmos_db_key == "cosmos_key"
            assert settings.cosmos_db_database_name == "chatbot"
            assert settings.cosmos_db_container_name == "conversations"

    def test_settings_model_dump(self):
        """Test settings serialization (excluding sensitive data)."""
        with patch.dict(
            os.environ,
            {
                "AZURE_OPENAI_API_KEY": "secret_key",
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
                "AZURE_OPENAI_DEPLOYMENT_NAME": "test-gpt-4",
            },
        ):
            settings = Settings()

            # Get settings as dict
            settings_dict = settings.model_dump()

            # Verify structure (API key should be included in dump)
            assert "azure_openai_api_key" in settings_dict
            assert "azure_openai_endpoint" in settings_dict
            assert "default_temperature" in settings_dict
            assert settings_dict["azure_openai_api_key"] == "secret_key"

    def test_settings_immutability(self):
        """Test that settings are properly configured as immutable."""
        with patch.dict(
            os.environ,
            {
                "AZURE_OPENAI_API_KEY": "test_key",
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
                "AZURE_OPENAI_DEPLOYMENT_NAME": "test-gpt-4",
            },
        ):
            settings = Settings()

            # Attempting to modify settings should raise an error
            with pytest.raises(ValidationError):
                settings.azure_openai_api_key = "new_key"

    def test_settings_repr_and_str(self):
        """Test string representations of settings."""
        with patch.dict(
            os.environ,
            {
                "AZURE_OPENAI_API_KEY": "test_key",
                "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
                "AZURE_OPENAI_DEPLOYMENT_NAME": "test-gpt-4",
            },
        ):
            settings = Settings()

            # Test string representation doesn't expose sensitive data
            settings_str = str(settings)
            settings_repr = repr(settings)

            # Should contain non-sensitive information
            assert "test-gpt-4" in settings_str
            assert "INFO" in settings_str  # log level

            # Verify it's actually a string representation
            assert isinstance(settings_str, str)
            assert isinstance(settings_repr, str)


class TestSettingsIntegration:
    """Test settings integration with the application."""

    def test_settings_with_complete_azure_configuration(self):
        """Test settings with complete Azure service configuration."""
        complete_env = {
            # OpenAI
            "AZURE_OPENAI_API_KEY": "openai_key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-4",
            "AZURE_OPENAI_API_VERSION": "2024-02-15-preview",
            # Search
            "AZURE_SEARCH_ENDPOINT": "https://test.search.windows.net",
            "AZURE_SEARCH_API_KEY": "search_key",
            "AZURE_SEARCH_INDEX_NAME": "knowledge-base",
            # Cosmos DB
            "COSMOS_DB_ENDPOINT": "https://test.documents.azure.com:443/",
            "COSMOS_DB_KEY": "cosmos_key",
            "COSMOS_DB_DATABASE_NAME": "chatbot",
            "COSMOS_DB_CONTAINER_NAME": "conversations",
            # Application
            "LOG_LEVEL": "DEBUG",
            "DEBUG": "true",
            "DEFAULT_TEMPERATURE": "0.8",
            "DEFAULT_MAX_TOKENS": "3000",
        }

        with patch.dict(os.environ, complete_env):
            settings = Settings()

            # Verify all configurations are loaded
            assert settings.azure_openai_api_key == "openai_key"
            assert settings.azure_search_endpoint == "https://test.search.windows.net"
            assert (
                settings.cosmos_db_endpoint == "https://test.documents.azure.com:443/"
            )
            assert settings.debug is True
            assert settings.log_level == "DEBUG"

    def test_production_vs_development_settings(self):
        """Test different configurations for production vs development."""
        # Development settings
        dev_env = {
            "AZURE_OPENAI_API_KEY": "dev_key",
            "AZURE_OPENAI_ENDPOINT": "https://dev.openai.azure.com/",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "dev-gpt-4",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG",
        }

        with patch.dict(os.environ, dev_env):
            dev_settings = Settings()
            assert dev_settings.debug is True
            assert dev_settings.log_level == "DEBUG"

        # Production settings
        prod_env = {
            "AZURE_OPENAI_API_KEY": "prod_key",
            "AZURE_OPENAI_ENDPOINT": "https://prod.openai.azure.com/",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "prod-gpt-4",
            "DEBUG": "false",
            "LOG_LEVEL": "WARNING",
        }

        with patch.dict(os.environ, prod_env):
            prod_settings = Settings()
            assert prod_settings.debug is False
            assert prod_settings.log_level == "WARNING"
