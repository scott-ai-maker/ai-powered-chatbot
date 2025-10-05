"""
Pytest configuration and shared fixtures for testing.

This module provides comprehensive testing infrastructure including:
- Test settings and environment setup
- Mock clients and services for Azure integrations
- Sample data factories for consistent test data
- Performance timing utilities
- Error simulation helpers

The fixtures are designed to be reusable across unit and integration tests.
"""

import pytest
import asyncio
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
import time
from requests.exceptions import HTTPError

from src.config.settings import Settings
from src.models.chat_models import ChatMessage, ChatResponse, ChatRequest

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
import httpx

from src.config.settings import Settings
from src.services.ai_service import AzureOpenAIService
from src.models.chat_models import ChatMessage, ChatResponse


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with mock values."""
    return Settings(
        # Required settings with test values
        secret_key="test-secret-key",
        azure_openai_endpoint="https://test-openai.openai.azure.com/",
        azure_openai_key="test-key-123",
        azure_search_endpoint="https://test-search.search.windows.net",
        azure_search_key="test-search-key",
        azure_cosmos_endpoint="https://test-cosmos.documents.azure.com:443/",
        azure_cosmos_key="test-cosmos-key",
        
        # Optional settings
        debug=True,
        log_level="DEBUG",
        app_name="AI Career Mentor Chatbot (Test)",
        app_version="0.1.0-test"
    )


@pytest.fixture
def sample_chat_message() -> ChatMessage:
    """Create a sample chat message for testing."""
    return ChatMessage(
        content="How do I transition to AI engineering?",
        role="user"
    )


@pytest.fixture
def sample_chat_response() -> ChatResponse:
    """Create a sample chat response for testing."""
    return ChatResponse(
        message="To transition to AI engineering, I recommend starting with...",
        conversation_id="test-conv-123",
        model_used="gpt-4",
        processing_time_ms=1500,
        confidence_score=0.95,
        response_type="career_advice"
    )


@pytest.fixture
def mock_openai_client():
    """Create a mock Azure OpenAI client."""
    mock_client = AsyncMock()
    
    # Mock chat completion response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test AI response"
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage.prompt_tokens = 50
    mock_response.usage.completion_tokens = 100
    mock_response.usage.total_tokens = 150
    
    mock_client.chat.completions.create.return_value = mock_response
    
    return mock_client


@pytest.fixture
async def ai_service_with_mock_client(test_settings, mock_openai_client):
    """Create an AI service with mocked OpenAI client."""
    service = AzureOpenAIService(test_settings)
    service.client = mock_openai_client
    return service


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client for testing API endpoints."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    return mock_client


@pytest.fixture
def test_conversation_data():
    """Provide test conversation data."""
    return {
        "conversation_id": "test-conv-123",
        "user_id": "test-user-456",
        "messages": [
            {
                "role": "user",
                "content": "How do I get started in AI?",
                "timestamp": "2025-10-04T10:00:00Z"
            },
            {
                "role": "assistant", 
                "content": "To get started in AI, I recommend...",
                "timestamp": "2025-10-04T10:00:02Z"
            }
        ]
    }


class AsyncContextManagerMock:
    """Helper class for mocking async context managers."""
    
    def __init__(self, return_value=None):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value or self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_async_context():
    """Create a mock async context manager."""
    return AsyncContextManagerMock


# Test data factories
class TestDataFactory:
    """Factory for creating test data objects."""
    
    @staticmethod
    def create_chat_message(
        content: str = "Test message",
        role: str = "user",
        **kwargs
    ) -> ChatMessage:
        """Create a test chat message."""
        defaults = {
            "content": content,
            "role": role
        }
        defaults.update(kwargs)
        return ChatMessage(**defaults)
    
    @staticmethod
    def create_chat_response(
        message: str = "Test response",
        conversation_id: str = "test-conv",
        **kwargs
    ) -> ChatResponse:
        """Create a test chat response."""
        defaults = {
            "message": message,
            "conversation_id": conversation_id,
            "model_used": "gpt-4-test",
            "processing_time_ms": 1000,
            "confidence_score": 0.9,
            "response_type": "career_advice"
        }
        defaults.update(kwargs)
        return ChatResponse(**defaults)


@pytest.fixture
def test_data_factory():
    """Provide the test data factory."""
    return TestDataFactory


# Async test utilities
@pytest_asyncio.fixture
async def async_test_client():
    """Create an async test client for FastAPI testing."""
    from fastapi.testclient import TestClient
    from src.main import app
    
    # Note: In a real implementation, you might use httpx.AsyncClient
    # for true async testing, but TestClient works for most cases
    return TestClient(app)


# Performance testing utilities
@pytest.fixture
def performance_timer():
    """Fixture for measuring test performance."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Database mocking (for future use)
@pytest.fixture
def mock_database():
    """Mock database connection for testing."""
    mock_db = MagicMock()
    mock_db.get_conversation.return_value = None
    mock_db.save_conversation.return_value = True
    return mock_db


# Error simulation fixtures
@pytest.fixture
def simulate_network_error():
    """Fixture to simulate network errors for testing error handling."""
    def _simulate_error(error_type="timeout"):
        if error_type == "timeout":
            return TimeoutError("Network timeout")
        elif error_type == "connection":
            return ConnectionError("Connection failed")
        elif error_type == "http":
            return HTTPError("HTTP error occurred")
        else:
            return Exception("Unknown network error")
    
    return _simulate_error


@pytest.fixture
def mock_streaming_response():
    """Mock streaming response from OpenAI."""
    class MockStreamChunk:
        def __init__(self, chunk_data):
            self.id = chunk_data.get("id", "")
            self.choices = [type('MockChoice', (), {
                'delta': type('MockDelta', (), choice.get('delta', {}))(),
                'finish_reason': choice.get('finish_reason')
            })() for choice in chunk_data.get('choices', [])]
    
    async def stream_generator():
        chunks = [
            {"id": "chunk_1", "choices": [{"delta": {"content": "Hello"}}]},
            {"id": "chunk_2", "choices": [{"delta": {"content": " world"}}]},
            {"id": "chunk_3", "choices": [{"delta": {"content": "!"}}]},
            {"id": "chunk_final", "choices": [{"delta": {}}], "finish_reason": "stop"}
        ]
        for chunk_data in chunks:
            yield MockStreamChunk(chunk_data)
    
    return stream_generator()


# Test markers for categorizing tests
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that test individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that test component interaction"
    )
    config.addinivalue_line(
        "markers", "async_test: Tests that use async/await patterns"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer to run"
    )
    config.addinivalue_line(
        "markers", "requires_azure: Tests that need real Azure credentials"
    )