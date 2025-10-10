"""
Integration tests for API endpoints.

These tests demonstrate comprehensive testing of FastAPI endpoints,
including request/response validation, error handling, authentication,
and integration with services. They show professional API testing practices.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime

from src.main import app
from src.models.chat_models import ChatResponse, HealthCheckResponse


class TestHealthEndpoint:
    """Test the health check endpoint."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_health_check_success(self, client):
        """Test successful health check."""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert "azure_openai_status" in data
        assert "database_status" in data

        # Verify data types
        assert isinstance(data["status"], str)
        assert isinstance(data["version"], str)
        assert isinstance(data["timestamp"], str)

        # Verify timestamp is valid ISO format
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

    def test_health_check_response_model(self, client):
        """Test that health check response matches our model."""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()

        # Should be able to create a HealthCheckResponse from the data
        health_response = HealthCheckResponse(**data)
        assert health_response.status in ["healthy", "degraded", "unhealthy"]
        assert health_response.version is not None

    @patch("src.services.ai_service.AzureOpenAIService")
    def test_health_check_with_service_error(self, mock_service_class, client):
        """Test health check when AI service has issues."""
        # Mock the service to raise an error during health check
        mock_service = AsyncMock()
        mock_service.health_check.side_effect = Exception("Service unavailable")
        mock_service_class.return_value = mock_service

        response = client.get("/api/health")

        # Should still return 200 but with degraded status
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["degraded", "unhealthy"]


class TestChatEndpoint:
    """Test the chat endpoint."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def valid_chat_request(self):
        """Create a valid chat request payload."""
        return {
            "message": "How do I transition to AI engineering?",
            "user_id": "user_123",
            "conversation_id": "conv_456",
        }

    @pytest.fixture
    def mock_chat_response(self):
        """Create a mock chat response."""
        return ChatResponse(
            message="To transition to AI engineering, I recommend...",
            conversation_id="conv_456",
            ai_model="gpt-4",
            processing_time_ms=1500,
            token_usage={
                "prompt_tokens": 50,
                "completion_tokens": 100,
                "total_tokens": 150,
            },
        )

    @patch("src.main.ai_service")
    async def test_chat_endpoint_success(
        self, mock_service, client, valid_chat_request, mock_chat_response
    ):
        """Test successful chat endpoint call."""
        # Mock the AI service response
        mock_service.generate_response = AsyncMock(return_value=mock_chat_response)

        response = client.post("/api/chat", json=valid_chat_request)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "message" in data
        assert "conversation_id" in data
        assert "model_used" in data
        assert "processing_time_ms" in data
        assert "token_usage" in data

        # Verify content
        assert data["message"] == mock_chat_response.message
        assert data["conversation_id"] == mock_chat_response.conversation_id
        assert data["token_usage"] == mock_chat_response.token_usage

    def test_chat_endpoint_missing_message(self, client):
        """Test chat endpoint with missing message."""
        invalid_request = {
            "user_id": "user_123"
            # Missing required 'message' field
        }

        response = client.post("/api/chat", json=invalid_request)

        assert response.status_code == 422  # Unprocessable Entity
        data = response.json()
        assert "detail" in data

        # Should mention the missing field
        error_details = str(data["detail"])
        assert "message" in error_details.lower()

    def test_chat_endpoint_missing_user_id(self, client):
        """Test chat endpoint with missing user_id."""
        invalid_request = {
            "message": "Test message"
            # Missing required 'user_id' field
        }

        response = client.post("/api/chat", json=invalid_request)

        assert response.status_code == 422
        data = response.json()

        error_details = str(data["detail"])
        assert "user_id" in error_details.lower()

    def test_chat_endpoint_empty_message(self, client):
        """Test chat endpoint with empty message."""
        invalid_request = {"message": "", "user_id": "user_123"}

        response = client.post("/api/chat", json=invalid_request)

        assert response.status_code == 422

    def test_chat_endpoint_whitespace_message(self, client):
        """Test chat endpoint with whitespace-only message."""
        invalid_request = {"message": "   \n\t  ", "user_id": "user_123"}

        response = client.post("/api/chat", json=invalid_request)

        assert response.status_code == 422

    def test_chat_endpoint_invalid_temperature(self, client):
        """Test chat endpoint with invalid temperature."""
        invalid_request = {
            "message": "Test message",
            "user_id": "user_123",
            "temperature": 3.0,  # Too high
        }

        response = client.post("/api/chat", json=invalid_request)

        assert response.status_code == 422

    def test_chat_endpoint_invalid_max_tokens(self, client):
        """Test chat endpoint with invalid max_tokens."""
        invalid_request = {
            "message": "Test message",
            "user_id": "user_123",
            "max_tokens": 0,  # Too low
        }

        response = client.post("/api/chat", json=invalid_request)

        assert response.status_code == 422

    @patch("src.main.ai_service")
    async def test_chat_endpoint_service_error(
        self, mock_service, client, valid_chat_request
    ):
        """Test chat endpoint when AI service raises an error."""
        # Mock the AI service to raise an error
        mock_service.generate_response = AsyncMock(
            side_effect=Exception("AI service error")
        )

        response = client.post("/api/chat", json=valid_chat_request)

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"].lower()

    def test_chat_endpoint_optional_parameters(self, client):
        """Test chat endpoint with optional parameters."""
        request_with_options = {
            "message": "Test message",
            "user_id": "user_123",
            "conversation_id": "conv_789",
            "temperature": 0.8,
            "max_tokens": 2000,
            "stream": False,
        }

        # This should pass validation even if the service isn't mocked
        # (it will fail at service level, but validation should pass)
        response = client.post("/api/chat", json=request_with_options)

        # Should pass validation (422 would indicate validation failure)
        assert response.status_code != 422

    @patch("src.main.ai_service")
    async def test_chat_endpoint_with_conversation_history(
        self, mock_service, client, mock_chat_response
    ):
        """Test chat endpoint with existing conversation."""
        mock_service.generate_response = AsyncMock(return_value=mock_chat_response)

        request = {
            "message": "Follow-up question",
            "user_id": "user_123",
            "conversation_id": "existing_conv",
        }

        response = client.post("/api/chat", json=request)

        assert response.status_code == 200

        # Verify service was called with the conversation_id
        call_args = mock_service.generate_response.call_args[0][0]
        assert call_args.conversation_id == "existing_conv"


class TestChatStreamingEndpoint:
    """Test the streaming chat endpoint."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def streaming_request(self):
        """Create a streaming chat request."""
        return {
            "message": "Tell me about AI careers",
            "user_id": "user_123",
            "stream": True,
        }

    @patch("src.main.ai_service")
    async def test_streaming_chat_endpoint(
        self, mock_service, client, streaming_request, mock_streaming_response
    ):
        """Test streaming chat endpoint."""
        # Mock the streaming response
        mock_service.generate_streaming_response = AsyncMock(
            return_value=mock_streaming_response
        )

        response = client.post("/api/chat", json=streaming_request)

        # For streaming, we expect a different response
        # (This test may need adjustment based on actual streaming implementation)
        assert response.status_code in [200, 206]  # 206 for partial content

    def test_streaming_request_validation(self, client):
        """Test that streaming requests are properly validated."""
        streaming_request = {
            "message": "Test streaming",
            "user_id": "user_123",
            "stream": True,
            "temperature": 0.7,
        }

        response = client.post("/api/chat", json=streaming_request)

        # Should pass validation
        assert response.status_code != 422


class TestAPIErrorHandling:
    """Test API error handling and edge cases."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_invalid_json_request(self, client):
        """Test handling of invalid JSON."""
        response = client.post(
            "/api/chat",
            data="invalid json content",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_unsupported_media_type(self, client):
        """Test handling of unsupported content type."""
        response = client.post(
            "/api/chat", data="some data", headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 422

    def test_request_too_large(self, client):
        """Test handling of very large requests."""
        # Create a very large message
        large_message = "x" * 10000  # Assuming this exceeds our limits

        request = {"message": large_message, "user_id": "user_123"}

        response = client.post("/api/chat", json=request)

        # Should be rejected due to validation
        assert response.status_code == 422

    def test_nonexistent_endpoint(self, client):
        """Test calling non-existent endpoint."""
        response = client.get("/api/nonexistent")

        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test using wrong HTTP method."""
        response = client.get("/api/chat")  # Should be POST

        assert response.status_code == 405


class TestAPICORS:
    """Test CORS configuration."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_cors_preflight_request(self, client):
        """Test CORS preflight request."""
        response = client.options(
            "/api/chat",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        # Should allow the request
        assert response.status_code == 200

        # Check CORS headers
        headers = response.headers
        assert "Access-Control-Allow-Origin" in headers
        assert "Access-Control-Allow-Methods" in headers

    def test_cors_actual_request(self, client):
        """Test actual request with CORS headers."""
        request_data = {"message": "Test message", "user_id": "user_123"}

        response = client.post(
            "/api/chat", json=request_data, headers={"Origin": "http://localhost:3000"}
        )

        # Should include CORS headers in response
        assert "Access-Control-Allow-Origin" in response.headers


class TestAPIDocumentation:
    """Test API documentation endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_openapi_schema(self, client):
        """Test OpenAPI schema endpoint."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()

        # Verify basic OpenAPI structure
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

        # Verify our endpoints are documented
        assert "/api/health" in schema["paths"]
        assert "/api/chat" in schema["paths"]

    def test_swagger_ui(self, client):
        """Test Swagger UI endpoint."""
        response = client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_ui(self, client):
        """Test ReDoc UI endpoint."""
        response = client.get("/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
