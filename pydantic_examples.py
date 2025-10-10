"""
Understanding Pydantic Settings - Examples and Patterns

This module demonstrates how Pydantic Settings provides type-safe,
validated configuration management that's used by companies like
Netflix, Uber, and other major tech companies.
"""

from typing import List
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


# ============================================================================
# BASIC PYDANTIC MODEL (NOT SETTINGS)
# ============================================================================


class User(BaseModel):
    """Regular Pydantic model for data validation."""

    name: str
    age: int
    email: str
    is_active: bool = True

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email address")
        return v


def pydantic_model_example():
    """Show how regular Pydantic models work."""
    print("🏗️ PYDANTIC MODEL EXAMPLE")
    print("-" * 40)

    # Valid data
    try:
        user = User(name="Scott", age=25, email="scott@example.com")
        print(f"✅ Valid user: {user}")
        print(f"   Type of age: {type(user.age)}")  # Automatically converted to int
    except Exception as e:
        print(f"❌ Error: {e}")

    # Invalid data - shows validation
    try:
        User(
            name="John",
            age="not-a-number",  # type: ignore[arg-type] # Intentionally invalid for demo
            email="invalid-email",  # This will also fail
        )
    except Exception as e:
        print(f"❌ Validation Error: {e}")


# ============================================================================
# PYDANTIC SETTINGS (THE MAGIC PART)
# ============================================================================


class DatabaseSettings(BaseSettings):
    """Database configuration with automatic environment loading."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # These will automatically load from environment variables
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "mydb"  # Default for development
    db_user: str = "user"  # Default for development
    db_password: str = "password"  # Default for development

    # Optional settings with defaults
    db_pool_size: int = 10
    db_timeout: float = 30.0

    @field_validator("db_port")
    @classmethod
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @property
    def connection_string(self) -> str:
        """Generate database connection string."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


class AIServiceSettings(BaseSettings):
    """AI service configuration - similar to our chatbot config."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Azure OpenAI settings
    openai_endpoint: str = "https://your-openai.openai.azure.com/"
    openai_key: str = "your-openai-key"
    openai_model: str = "gpt-4"

    # Chat settings
    max_tokens: int = 1000
    temperature: float = 0.7
    system_prompt: str = "You are a helpful AI career mentor."

    # Advanced settings
    allowed_domains: str = "localhost,127.0.0.1"
    rate_limit: int = 100
    debug_mode: bool = False

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v):
        if not 0 <= v <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        return v

    @property
    def allowed_domains_list(self) -> List[str]:
        """Convert comma-separated domains to list."""
        return [domain.strip() for domain in self.allowed_domains.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False  # Environment variables are case-insensitive


# ============================================================================
# DEMONSTRATING DIFFERENT WAYS TO LOAD SETTINGS
# ============================================================================


def demonstrate_settings_loading():
    """Show different ways Pydantic Settings loads configuration."""
    print("\n⚙️ PYDANTIC SETTINGS LOADING EXAMPLES")
    print("-" * 50)

    # Method 1: From environment variables
    print("1. Loading from environment variables:")
    os.environ["OPENAI_ENDPOINT"] = "https://test-openai.azure.com"
    os.environ["OPENAI_KEY"] = "test-key-123"
    os.environ["DEBUG"] = "true"  # String -> bool conversion
    os.environ["MAX_TOKENS"] = "1500"  # String -> int conversion
    os.environ["TEMPERATURE"] = "0.8"  # String -> float conversion

    try:
        settings = AIServiceSettings()
        print(f"  ✅ OpenAI Endpoint: {settings.openai_endpoint}")
        print(
            f"  ✅ Max Tokens: {settings.max_tokens} (type: {type(settings.max_tokens)})"
        )
        print(
            f"  ✅ Temperature: {settings.temperature} (type: {type(settings.temperature)})"
        )
        print(
            f"  ✅ Debug Mode: {settings.debug_mode} (type: {type(settings.debug_mode)})"
        )
        print(f"  ✅ Allowed Domains: {settings.allowed_domains_list}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

    # Method 2: Show validation in action
    print("\n2. Validation example:")
    os.environ["TEMPERATURE"] = "5.0"  # Invalid temperature
    try:
        AIServiceSettings()
    except Exception as e:
        print(f"  ❌ Validation caught invalid temperature: {e}")

    # Reset for next example
    os.environ["TEMPERATURE"] = "0.8"


# ============================================================================
# WHY THIS PATTERN IS POWERFUL
# ============================================================================


def why_pydantic_settings_rocks():
    """Explain the benefits of this pattern."""
    print("\n🚀 WHY PYDANTIC SETTINGS IS AMAZING")
    print("-" * 40)

    benefits = [
        "✅ Type Safety: Automatic conversion and validation",
        "✅ Environment Variables: Automatic loading from .env files",
        "✅ Documentation: Self-documenting configuration",
        "✅ IDE Support: Full autocompletion and type hints",
        "✅ Testing: Easy to override settings for tests",
        "✅ Production Ready: Used by major companies",
        "✅ Validation: Custom validators catch errors early",
        "✅ Flexibility: Multiple sources (env vars, files, code)",
    ]

    for benefit in benefits:
        print(f"  {benefit}")

    print("\n🏢 ENTERPRISE PATTERNS:")
    print("  • Netflix: Uses similar patterns for microservice config")
    print("  • Uber: Pydantic for API validation and settings")
    print("  • Instagram: Type-safe configuration management")
    print("  • Reddit: Pydantic Settings for service configuration")


# ============================================================================
# COMPARISON WITH OUR CHATBOT SETTINGS
# ============================================================================


def compare_with_our_chatbot():
    """Show how this relates to our chatbot configuration."""
    print("\n🤖 OUR CHATBOT SETTINGS PATTERN")
    print("-" * 35)

    # Import our actual settings
    from src.config.settings import get_settings

    try:
        our_settings = get_settings()
        print("✅ Our chatbot settings loaded successfully!")
        print(f"  App Name: {our_settings.app_name}")
        print(f"  Debug Mode: {our_settings.debug}")
        print(f"  Allowed Hosts: {our_settings.allowed_hosts_list}")
        print(f"  OpenAI Deployment: {our_settings.azure_openai_deployment_name}")
        print(f"  Temperature: {our_settings.default_temperature}")

        print("\n🔧 Key Features in Our Implementation:")
        print("  • Automatic Azure credential loading")
        print("  • Validation for temperature, log levels, etc.")
        print("  • Production vs development configurations")
        print("  • Caching with @lru_cache for performance")
        print("  • FastAPI dependency injection ready")

    except Exception as e:
        print(f"❌ Error loading our settings: {e}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main():
    """Run all Pydantic examples."""
    pydantic_model_example()
    demonstrate_settings_loading()
    why_pydantic_settings_rocks()
    compare_with_our_chatbot()


if __name__ == "__main__":
    main()
