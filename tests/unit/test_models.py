"""
Unit tests for Pydantic models.

These tests ensure our data models work correctly with validation,
serialization, and edge cases. They demonstrate TDD practices and
comprehensive input validation testing.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.chat_models import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    StreamingChatChunk,
    HealthCheckResponse,
    ErrorResponse,
)


class TestChatMessage:
    """Test the ChatMessage model."""

    def test_valid_chat_message_creation(self):
        """Test creating a valid chat message."""
        message = ChatMessage(content="Hello, how can I help?", role="assistant")

        assert message.content == "Hello, how can I help?"
        assert message.role == "assistant"
        assert message.id is not None
        assert isinstance(message.timestamp, datetime)

    def test_chat_message_with_custom_id(self):
        """Test creating chat message with custom ID."""
        custom_id = "msg_123"
        message = ChatMessage(id=custom_id, content="Test message", role="user")

        assert message.id == custom_id

    def test_chat_message_role_validation(self):
        """Test that only valid roles are accepted."""
        # Valid roles
        for role in ["user", "assistant", "system"]:
            message = ChatMessage(content="Test", role=role)
            assert message.role == role

        # Invalid role should raise ValidationError
        with pytest.raises(ValidationError):
            ChatMessage(content="Test", role="invalid_role")

    def test_empty_content_validation(self):
        """Test that empty content raises ValidationError."""
        with pytest.raises(ValidationError):
            ChatMessage(content="", role="user")

    def test_content_length_validation(self):
        """Test content length limits."""
        # Valid length
        message = ChatMessage(content="x" * 4000, role="user")
        assert len(message.content) == 4000

        # Too long content
        with pytest.raises(ValidationError):
            ChatMessage(content="x" * 4001, role="user")

    def test_message_serialization(self):
        """Test message serialization to dict/JSON."""
        message = ChatMessage(content="Test", role="user")
        data = message.model_dump()

        assert "content" in data
        assert "role" in data
        assert "timestamp" in data
        assert "id" in data

        # Test JSON serialization
        json_str = message.model_dump_json()
        assert "Test" in json_str
        assert "user" in json_str


class TestChatRequest:
    """Test the ChatRequest model."""

    def test_valid_chat_request(self):
        """Test creating a valid chat request."""
        request = ChatRequest(message="How do I transition to AI?", user_id="user_123")

        assert request.message == "How do I transition to AI?"
        assert request.user_id == "user_123"
        assert request.conversation_id is None
        assert request.stream is False
        assert request.temperature is None
        assert request.max_tokens is None

    def test_chat_request_with_optional_fields(self):
        """Test chat request with all optional fields."""
        request = ChatRequest(
            message="Test message",
            user_id="user_123",
            conversation_id="conv_456",
            stream=True,
            temperature=0.8,
            max_tokens=2000,
        )

        assert request.conversation_id == "conv_456"
        assert request.stream is True
        assert request.temperature == 0.8
        assert request.max_tokens == 2000

    def test_message_whitespace_validation(self):
        """Test that whitespace-only messages are rejected."""
        with pytest.raises(ValidationError):
            ChatRequest(message="   ", user_id="user_123")

        with pytest.raises(ValidationError):
            ChatRequest(message="\n\t  \n", user_id="user_123")

    def test_message_length_validation(self):
        """Test message length constraints."""
        # Valid length
        request = ChatRequest(message="x" * 4000, user_id="user_123")
        assert len(request.message) == 4000

        # Too long
        with pytest.raises(ValidationError):
            ChatRequest(message="x" * 4001, user_id="user_123")

    def test_temperature_validation(self):
        """Test temperature parameter validation."""
        # Valid temperatures
        for temp in [0.0, 0.5, 1.0, 2.0]:
            request = ChatRequest(message="Test", user_id="user_123", temperature=temp)
            assert request.temperature == temp

        # Invalid temperatures
        for invalid_temp in [-0.1, 2.1, 5.0]:
            with pytest.raises(ValidationError):
                ChatRequest(
                    message="Test", user_id="user_123", temperature=invalid_temp
                )

    def test_max_tokens_validation(self):
        """Test max_tokens parameter validation."""
        # Valid values
        request = ChatRequest(message="Test", user_id="user_123", max_tokens=1000)
        assert request.max_tokens == 1000

        # Invalid values
        with pytest.raises(ValidationError):
            ChatRequest(message="Test", user_id="user_123", max_tokens=0)


class TestChatResponse:
    """Test the ChatResponse model."""

    def test_valid_chat_response(self):
        """Test creating a valid chat response."""
        response = ChatResponse(
            message="Here's my advice...",
            conversation_id="conv_123",
            model_used="gpt-4",
            processing_time_ms=1500,
        )

        assert response.message == "Here's my advice..."
        assert response.conversation_id == "conv_123"
        assert response.model_used == "gpt-4"
        assert response.processing_time_ms == 1500
        assert response.id is not None
        assert response.response_type == "career_advice"  # default value

    def test_response_with_metadata(self):
        """Test response with all metadata fields."""
        token_usage = {
            "prompt_tokens": 50,
            "completion_tokens": 100,
            "total_tokens": 150,
        }

        response = ChatResponse(
            message="Test response",
            conversation_id="conv_123",
            model_used="gpt-4",
            processing_time_ms=2000,
            token_usage=token_usage,
            confidence_score=0.95,
            response_type="clarification",
        )

        assert response.token_usage == token_usage
        assert response.confidence_score == 0.95
        assert response.response_type == "clarification"

    def test_confidence_score_validation(self):
        """Test confidence score validation."""
        # Valid scores
        for score in [0.0, 0.5, 1.0]:
            response = ChatResponse(
                message="Test",
                conversation_id="conv_123",
                model_used="gpt-4",
                processing_time_ms=1000,
                confidence_score=score,
            )
            assert response.confidence_score == score

        # Invalid scores
        for invalid_score in [-0.1, 1.1, 2.0]:
            with pytest.raises(ValidationError):
                ChatResponse(
                    message="Test",
                    conversation_id="conv_123",
                    model_used="gpt-4",
                    processing_time_ms=1000,
                    confidence_score=invalid_score,
                )

    def test_response_type_validation(self):
        """Test response type validation."""
        valid_types = ["career_advice", "general", "clarification"]

        for response_type in valid_types:
            response = ChatResponse(
                message="Test",
                conversation_id="conv_123",
                model_used="gpt-4",
                processing_time_ms=1000,
                response_type=response_type,
            )
            assert response.response_type == response_type

        # Invalid type
        with pytest.raises(ValidationError):
            ChatResponse(
                message="Test",
                conversation_id="conv_123",
                model_used="gpt-4",
                processing_time_ms=1000,
                response_type="invalid_type",
            )


class TestStreamingChatChunk:
    """Test the StreamingChatChunk model."""

    def test_valid_streaming_chunk(self):
        """Test creating a valid streaming chunk."""
        chunk = StreamingChatChunk(
            id="chunk_001", conversation_id="conv_123", content="Hello"
        )

        assert chunk.id == "chunk_001"
        assert chunk.conversation_id == "conv_123"
        assert chunk.content == "Hello"
        assert chunk.is_final is False

    def test_final_chunk(self):
        """Test creating a final streaming chunk."""
        chunk = StreamingChatChunk(
            id="chunk_final", conversation_id="conv_123", content="", is_final=True
        )

        assert chunk.is_final is True
        assert chunk.content == ""


class TestHealthCheckResponse:
    """Test the HealthCheckResponse model."""

    def test_healthy_status(self):
        """Test creating a healthy status response."""
        health = HealthCheckResponse(
            status="healthy",
            version="0.1.0",
            azure_openai_status="connected",
            database_status="connected",
        )

        assert health.status == "healthy"
        assert health.azure_openai_status == "connected"
        assert health.database_status == "connected"
        assert isinstance(health.timestamp, datetime)

    def test_status_validation(self):
        """Test status field validation."""
        valid_statuses = ["healthy", "degraded", "unhealthy"]

        for status in valid_statuses:
            health = HealthCheckResponse(
                status=status,
                version="0.1.0",
                azure_openai_status="connected",
                database_status="connected",
            )
            assert health.status == status

        # Invalid status
        with pytest.raises(ValidationError):
            HealthCheckResponse(
                status="invalid",
                version="0.1.0",
                azure_openai_status="connected",
                database_status="connected",
            )


class TestErrorResponse:
    """Test the ErrorResponse model."""

    def test_basic_error_response(self):
        """Test creating a basic error response."""
        error = ErrorResponse(
            error_code="INVALID_INPUT", message="The input provided is invalid"
        )

        assert error.error_code == "INVALID_INPUT"
        assert error.message == "The input provided is invalid"
        assert isinstance(error.timestamp, datetime)
        assert error.details is None
        assert error.request_id is None

    def test_error_with_details(self):
        """Test error response with additional details."""
        details = {"field": "message", "constraint": "min_length"}

        error = ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Validation failed",
            details=details,
            request_id="req_123",
        )

        assert error.details == details
        assert error.request_id == "req_123"


class TestModelIntegration:
    """Test integration between different models."""

    def test_chat_request_to_response_flow(self):
        """Test the typical request-response flow."""
        # Create a request
        request = ChatRequest(
            message="How do I learn AI?", user_id="user_123", conversation_id="conv_456"
        )

        # Simulate processing and create response
        response = ChatResponse(
            message="To learn AI, start with...",
            conversation_id=request.conversation_id,
            model_used="gpt-4",
            processing_time_ms=1200,
        )

        assert response.conversation_id == request.conversation_id
        assert len(response.message) > 0

    def test_streaming_chunks_sequence(self):
        """Test a sequence of streaming chunks."""
        conversation_id = "conv_789"

        # Create sequence of chunks
        chunks = [
            StreamingChatChunk(
                id="chunk_001",
                conversation_id=conversation_id,
                content="To learn",
                is_final=False,
            ),
            StreamingChatChunk(
                id="chunk_002",
                conversation_id=conversation_id,
                content=" AI engineering",
                is_final=False,
            ),
            StreamingChatChunk(
                id="chunk_final",
                conversation_id=conversation_id,
                content="",
                is_final=True,
            ),
        ]

        # Verify sequence properties
        assert all(chunk.conversation_id == conversation_id for chunk in chunks)
        assert chunks[-1].is_final is True
        assert all(not chunk.is_final for chunk in chunks[:-1])

        # Reconstruct message
        full_message = "".join(chunk.content for chunk in chunks if not chunk.is_final)
        assert full_message == "To learn AI engineering"
