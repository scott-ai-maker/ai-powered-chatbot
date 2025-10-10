"""
Integration tests for the full application stack.

These tests demonstrate end-to-end testing practices, testing the
complete request/response flow through all application layers.
They show how to test real-world scenarios and system integration.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import time

from src.main import app


class TestFullApplicationFlow:
    """Test complete application flow from request to response."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def complete_environment(self, monkeypatch):
        """Set up complete environment variables for testing."""
        env_vars = {
            "AZURE_OPENAI_API_KEY": "test_integration_key",
            "AZURE_OPENAI_ENDPOINT": "https://integration-test.openai.azure.com/",
            "AZURE_OPENAI_DEPLOYMENT_NAME": "integration-gpt-4",
            "LOG_LEVEL": "INFO",
            "DEBUG": "false",
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

    @patch("src.services.ai_service.AsyncAzureOpenAI")
    async def test_complete_chat_flow(
        self, mock_openai_class, client, complete_environment, mock_chat_completion
    ):
        """Test complete chat flow from API request to response."""
        # Set up mock OpenAI client
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_chat_completion
        )
        mock_openai_class.return_value = mock_client

        # Make chat request
        request_data = {
            "message": "How do I transition to AI engineering?",
            "user_id": "integration_user_123",
            "conversation_id": "integration_conv_456",
            "temperature": 0.7,
            "max_tokens": 2000,
        }

        response = client.post("/api/chat", json=request_data)

        # Verify response
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "message" in data
        assert "conversation_id" in data
        assert "model_used" in data
        assert "processing_time_ms" in data
        assert "token_usage" in data

        # Verify response content
        assert data["conversation_id"] == "integration_conv_456"
        assert data["message"] == mock_chat_completion.choices[0].message.content
        assert data["model_used"] == mock_chat_completion.model

        # Verify OpenAI client was called correctly
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]

        assert call_kwargs["model"] == "integration-gpt-4"
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["max_tokens"] == 2000
        assert len(call_kwargs["messages"]) >= 2  # System message + user message
        assert call_kwargs["messages"][-1]["content"] == request_data["message"]

    @patch("src.services.ai_service.AsyncAzureOpenAI")
    async def test_conversation_continuity(
        self, mock_openai_class, client, complete_environment, mock_chat_completion
    ):
        """Test conversation continuity across multiple messages."""
        # Set up mock
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_chat_completion
        )
        mock_openai_class.return_value = mock_client

        conversation_id = "continuity_test_conv"

        # First message
        first_request = {
            "message": "What is machine learning?",
            "user_id": "continuity_user",
            "conversation_id": conversation_id,
        }

        response1 = client.post("/api/chat", json=first_request)
        assert response1.status_code == 200

        # Second message in same conversation
        second_request = {
            "message": "Can you give me an example?",
            "user_id": "continuity_user",
            "conversation_id": conversation_id,
        }

        response2 = client.post("/api/chat", json=second_request)
        assert response2.status_code == 200

        # Verify both responses have same conversation_id
        data1 = response1.json()
        data2 = response2.json()
        assert data1["conversation_id"] == conversation_id
        assert data2["conversation_id"] == conversation_id

        # Verify second call included conversation history
        second_call_kwargs = mock_client.chat.completions.create.call_args_list[1][1]
        messages = second_call_kwargs["messages"]

        # Should have system message + previous user message + previous assistant response + new user message
        assert len(messages) >= 4
        assert any("What is machine learning?" in str(msg) for msg in messages)
        assert any("Can you give me an example?" in str(msg) for msg in messages)

    async def test_health_check_integration(self, client, complete_environment):
        """Test health check integration."""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()

        # Verify complete health check response
        required_fields = [
            "status",
            "version",
            "timestamp",
            "azure_openai_status",
            "database_status",
        ]

        for field in required_fields:
            assert field in data

        # Status should be one of the valid values
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert data["version"] is not None

    @patch("src.services.ai_service.AsyncAzureOpenAI")
    async def test_error_handling_integration(
        self, mock_openai_class, client, complete_environment
    ):
        """Test error handling through the full stack."""
        # Set up mock to raise an error
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("Integration test error")
        )
        mock_openai_class.return_value = mock_client

        request_data = {
            "message": "This should cause an error",
            "user_id": "error_test_user",
        }

        response = client.post("/api/chat", json=request_data)

        # Should return 500 error
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    def test_request_validation_integration(self, client, complete_environment):
        """Test request validation through the full stack."""
        # Test various invalid requests
        invalid_requests = [
            {},  # Empty request
            {"message": ""},  # Empty message
            {"message": "test"},  # Missing user_id
            {"user_id": "test"},  # Missing message
            {
                "message": "test",
                "user_id": "test",
                "temperature": 3.0,
            },  # Invalid temperature
            {
                "message": "test",
                "user_id": "test",
                "max_tokens": 0,
            },  # Invalid max_tokens
        ]

        for invalid_request in invalid_requests:
            response = client.post("/api/chat", json=invalid_request)
            assert response.status_code == 422, (
                f"Request should be invalid: {invalid_request}"
            )

    @patch("src.services.ai_service.AsyncAzureOpenAI")
    async def test_performance_measurement_integration(
        self, mock_openai_class, client, complete_environment, mock_chat_completion
    ):
        """Test that performance measurements work through the full stack."""
        # Add delay to mock to test timing
        mock_client = AsyncMock()

        async def delayed_response(*args, **kwargs):
            await asyncio.sleep(0.1)  # 100ms delay
            return mock_chat_completion

        mock_client.chat.completions.create = AsyncMock(side_effect=delayed_response)
        mock_openai_class.return_value = mock_client

        request_data = {
            "message": "Performance test message",
            "user_id": "perf_test_user",
        }

        start_time = time.time()
        response = client.post("/api/chat", json=request_data)
        end_time = time.time()

        assert response.status_code == 200
        data = response.json()

        # Verify processing time is reported
        assert "processing_time_ms" in data
        assert data["processing_time_ms"] > 0

        # Verify actual response time was reasonable
        actual_time_ms = (end_time - start_time) * 1000
        assert actual_time_ms >= 100  # Should be at least our delay

    def test_cors_integration(self, client, complete_environment):
        """Test CORS functionality in full integration."""
        # Test preflight request
        preflight_response = client.options(
            "/api/chat",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        assert preflight_response.status_code == 200
        assert "Access-Control-Allow-Origin" in preflight_response.headers

        # Test actual request with CORS
        request_data = {"message": "CORS test message", "user_id": "cors_test_user"}

        response = client.post(
            "/api/chat", json=request_data, headers={"Origin": "http://localhost:3000"}
        )

        # Should have CORS headers
        assert "Access-Control-Allow-Origin" in response.headers


class TestApplicationStateManagement:
    """Test application state management and lifecycle."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @patch("src.services.ai_service.AsyncAzureOpenAI")
    async def test_service_initialization_on_startup(
        self, mock_openai_class, client, monkeypatch
    ):
        """Test that services are properly initialized on startup."""
        # Set required environment variables
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "startup_test_key")
        monkeypatch.setenv(
            "AZURE_OPENAI_ENDPOINT", "https://startup-test.openai.azure.com/"
        )
        monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_NAME", "startup-gpt-4")

        # Make a request to trigger startup
        response = client.get("/api/health")

        # Should succeed, indicating services initialized
        assert response.status_code == 200

        # Verify OpenAI client was created
        mock_openai_class.assert_called()

    async def test_concurrent_requests_handling(self, client, monkeypatch):
        """Test handling of concurrent requests."""
        # Set up environment
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "concurrent_test_key")
        monkeypatch.setenv(
            "AZURE_OPENAI_ENDPOINT", "https://concurrent-test.openai.azure.com/"
        )
        monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_NAME", "concurrent-gpt-4")

        # Make multiple concurrent health check requests
        import concurrent.futures

        def make_request():
            return client.get("/api/health")

        # Execute 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # All requests should succeed
        assert all(result.status_code == 200 for result in results)

    @patch("src.services.ai_service.AsyncAzureOpenAI")
    async def test_memory_usage_across_conversations(
        self, mock_openai_class, client, monkeypatch, mock_chat_completion
    ):
        """Test memory usage with multiple conversations."""
        # Set up environment and mocks
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "memory_test_key")
        monkeypatch.setenv(
            "AZURE_OPENAI_ENDPOINT", "https://memory-test.openai.azure.com/"
        )
        monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_NAME", "memory-gpt-4")

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_chat_completion
        )
        mock_openai_class.return_value = mock_client

        # Create multiple conversations
        for conv_id in range(10):
            for msg_id in range(5):  # 5 messages per conversation
                request_data = {
                    "message": f"Message {msg_id} in conversation {conv_id}",
                    "user_id": f"user_{conv_id}",
                    "conversation_id": f"conv_{conv_id}",
                }

                response = client.post("/api/chat", json=request_data)
                assert response.status_code == 200

        # All requests should have succeeded without memory issues
        # This is a basic test - in a real scenario, you might want to
        # monitor actual memory usage or set limits


class TestRealWorldScenarios:
    """Test realistic usage scenarios."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def setup_environment(self, monkeypatch):
        """Set up realistic environment."""
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "realistic_test_key")
        monkeypatch.setenv(
            "AZURE_OPENAI_ENDPOINT", "https://realistic-test.openai.azure.com/"
        )
        monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_NAME", "realistic-gpt-4")
        monkeypatch.setenv("LOG_LEVEL", "INFO")

    @patch("src.services.ai_service.AsyncAzureOpenAI")
    async def test_typical_career_consultation_flow(
        self, mock_openai_class, client, setup_environment, mock_chat_completion
    ):
        """Test a typical career consultation conversation flow."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_chat_completion
        )
        mock_openai_class.return_value = mock_client

        conversation_id = "career_consultation_001"
        user_id = "career_seeker_123"

        # Typical conversation flow
        conversation_steps = [
            "Hi, I'm interested in transitioning to AI engineering. Can you help?",
            "I have a background in software development with 3 years of experience in Python.",
            "What specific skills should I focus on learning first?",
            "How long does it typically take to make this transition?",
            "What are some good resources for learning machine learning?",
            "Should I get a master's degree or can I learn through online courses?",
            "What kind of projects should I build for my portfolio?",
            "How do I prepare for AI engineering interviews?",
            "Thank you for the advice!",
        ]

        responses = []
        for step, message in enumerate(conversation_steps):
            request_data = {
                "message": message,
                "user_id": user_id,
                "conversation_id": conversation_id,
            }

            response = client.post("/api/chat", json=request_data)
            assert response.status_code == 200

            data = response.json()
            responses.append(data)

            # Verify conversation continuity
            assert data["conversation_id"] == conversation_id
            assert "message" in data
            assert data["processing_time_ms"] > 0

        # Verify all responses were successful
        assert len(responses) == len(conversation_steps)

        # Verify conversation history grew appropriately
        # (This would need access to the actual service to verify history length)

    @patch("src.services.ai_service.AsyncAzureOpenAI")
    async def test_multiple_users_concurrent_conversations(
        self, mock_openai_class, client, setup_environment, mock_chat_completion
    ):
        """Test multiple users having concurrent conversations."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_chat_completion
        )
        mock_openai_class.return_value = mock_client

        # Simulate 3 users having concurrent conversations
        users = [
            {
                "user_id": "user_001",
                "conv_id": "conv_001",
                "topic": "AI career transition",
            },
            {
                "user_id": "user_002",
                "conv_id": "conv_002",
                "topic": "Machine learning skills",
            },
            {
                "user_id": "user_003",
                "conv_id": "conv_003",
                "topic": "Data science path",
            },
        ]

        # Each user sends multiple messages
        import concurrent.futures

        def user_conversation(user_info):
            messages = [
                f"I want to learn about {user_info['topic']}",
                "Can you give me more details?",
                "What are the prerequisites?",
                "Thank you for the information",
            ]

            user_responses = []
            for message in messages:
                request_data = {
                    "message": message,
                    "user_id": user_info["user_id"],
                    "conversation_id": user_info["conv_id"],
                }

                response = client.post("/api/chat", json=request_data)
                user_responses.append(response)

            return user_responses

        # Execute concurrent conversations
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(user_conversation, user) for user in users]
            all_responses = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # Verify all conversations succeeded
        for user_responses in all_responses:
            assert len(user_responses) == 4  # 4 messages per user
            assert all(response.status_code == 200 for response in user_responses)

            # Verify conversation IDs are maintained
            conv_ids = [
                response.json()["conversation_id"] for response in user_responses
            ]
            assert len(set(conv_ids)) == 1  # All responses should have same conv_id

    def test_api_documentation_accessibility(self, client, setup_environment):
        """Test that API documentation is accessible and complete."""
        # Test OpenAPI schema
        schema_response = client.get("/openapi.json")
        assert schema_response.status_code == 200

        schema = schema_response.json()

        # Verify schema completeness
        assert "info" in schema
        assert "paths" in schema
        assert "components" in schema

        # Verify our endpoints are documented
        paths = schema["paths"]
        assert "/api/health" in paths
        assert "/api/chat" in paths

        # Verify endpoint documentation includes required information
        chat_endpoint = paths["/api/chat"]["post"]
        assert "summary" in chat_endpoint
        assert "requestBody" in chat_endpoint
        assert "responses" in chat_endpoint

        # Test Swagger UI accessibility
        swagger_response = client.get("/docs")
        assert swagger_response.status_code == 200

        # Test ReDoc accessibility
        redoc_response = client.get("/redoc")
        assert redoc_response.status_code == 200
