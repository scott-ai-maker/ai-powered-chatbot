"""
Unit tests for the AzureOpenAIService.

These tests demonstrate comprehensive testing of async services,
proper mocking strategies, error handling, and streaming functionality.
They show professional testing practices for AI service layers.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai._exceptions import APIError, RateLimitError, APITimeoutError

from src.services.ai_service import AzureOpenAIService
from src.models.chat_models import ChatMessage, ChatRequest


class TestAzureOpenAIService:
    """Test the AzureOpenAIService class."""

    @pytest.fixture
    def service(self, test_settings, mock_openai_client):
        """Create an AI service instance for testing."""
        return AzureOpenAIService(test_settings)

    @pytest.fixture
    def sample_chat_request(self):
        """Create a sample chat request for testing."""
        return ChatRequest(
            message="How do I transition to AI engineering?",
            user_id="user_123",
            conversation_id="conv_456",
        )

    @pytest.fixture
    def mock_chat_completion(self):
        """Create a mock ChatCompletion response."""
        return ChatCompletion(
            id="chatcmpl-123",
            object="chat.completion",
            created=1677652288,
            model="gpt-4",
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(
                        role="assistant",
                        content="To transition to AI engineering, I recommend starting with...",
                    ),
                    finish_reason="stop",
                )
            ],
            usage={"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150},
        )

    async def test_service_initialization(self, test_settings):
        """Test service initialization with settings."""
        service = AzureOpenAIService(test_settings)

        assert service.settings == test_settings
        assert service.client is not None
        assert service.conversation_history == {}

    async def test_generate_response_success(
        self, service, sample_chat_request, mock_chat_completion
    ):
        """Test successful response generation."""
        # Mock the OpenAI client call
        service.client.chat.completions.create = AsyncMock(
            return_value=mock_chat_completion
        )

        # Generate response
        response = await service.generate_response(sample_chat_request)

        # Verify response
        assert response.message == mock_chat_completion.choices[0].message.content
        assert response.conversation_id == sample_chat_request.conversation_id
        assert response.model_used == mock_chat_completion.model
        assert response.processing_time_ms > 0
        assert response.token_usage == {
            "prompt_tokens": 50,
            "completion_tokens": 100,
            "total_tokens": 150,
        }

        # Verify OpenAI was called correctly
        service.client.chat.completions.create.assert_called_once()
        call_args = service.client.chat.completions.create.call_args
        assert call_args[1]["model"] == service.settings.azure_openai_deployment_name
        assert call_args[1]["messages"][-1]["content"] == sample_chat_request.message

    async def test_generate_response_with_conversation_history(
        self, service, sample_chat_request, mock_chat_completion
    ):
        """Test response generation with existing conversation history."""
        # Add some conversation history
        conv_id = sample_chat_request.conversation_id
        service.conversation_history[conv_id] = [
            ChatMessage(content="Hello", role="user"),
            ChatMessage(content="Hi there!", role="assistant"),
        ]

        service.client.chat.completions.create = AsyncMock(
            return_value=mock_chat_completion
        )

        await service.generate_response(sample_chat_request)

        # Verify history was included in the call
        call_args = service.client.chat.completions.create.call_args
        messages = call_args[1]["messages"]

        # Should have system message + 2 history messages + new message
        assert len(messages) >= 4
        assert messages[-1]["content"] == sample_chat_request.message
        assert any(msg["content"] == "Hello" for msg in messages)
        assert any(msg["content"] == "Hi there!" for msg in messages)

    async def test_generate_response_with_custom_parameters(
        self, service, mock_chat_completion
    ):
        """Test response generation with custom parameters."""
        request = ChatRequest(
            message="Test message", user_id="user_123", temperature=0.8, max_tokens=2000
        )

        service.client.chat.completions.create = AsyncMock(
            return_value=mock_chat_completion
        )

        await service.generate_response(request)

        # Verify custom parameters were used
        call_args = service.client.chat.completions.create.call_args
        assert call_args[1]["temperature"] == 0.8
        assert call_args[1]["max_tokens"] == 2000

    async def test_generate_response_api_error(self, service, sample_chat_request):
        """Test handling of OpenAI API errors."""
        # Mock API error
        service.client.chat.completions.create = AsyncMock(
            side_effect=APIError("API Error occurred")
        )

        with pytest.raises(APIError):
            await service.generate_response(sample_chat_request)

    async def test_generate_response_rate_limit_error(
        self, service, sample_chat_request
    ):
        """Test handling of rate limit errors."""
        service.client.chat.completions.create = AsyncMock(
            side_effect=RateLimitError("Rate limit exceeded", response=None, body=None)
        )

        with pytest.raises(RateLimitError):
            await service.generate_response(sample_chat_request)

    async def test_generate_response_timeout_error(self, service, sample_chat_request):
        """Test handling of timeout errors."""
        service.client.chat.completions.create = AsyncMock(
            side_effect=APITimeoutError("Request timed out")
        )

        with pytest.raises(APITimeoutError):
            await service.generate_response(sample_chat_request)

    async def test_conversation_history_management(self, service):
        """Test conversation history is properly managed."""
        conv_id = "test_conv_123"
        request = ChatRequest(
            message="First message", user_id="user_123", conversation_id=conv_id
        )

        # Mock successful response
        mock_completion = ChatCompletion(
            id="chatcmpl-123",
            object="chat.completion",
            created=1677652288,
            model="gpt-4",
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(
                        role="assistant", content="First response"
                    ),
                    finish_reason="stop",
                )
            ],
            usage={"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
        )

        service.client.chat.completions.create = AsyncMock(return_value=mock_completion)

        # Generate first response
        await service.generate_response(request)

        # Check conversation history was created and updated
        assert conv_id in service.conversation_history
        history = service.conversation_history[conv_id]
        assert len(history) == 2  # User message + assistant response
        assert history[0].content == "First message"
        assert history[0].role == "user"
        assert history[1].content == "First response"
        assert history[1].role == "assistant"

        # Send second message
        request.message = "Second message"
        await service.generate_response(request)

        # Verify history grew
        history = service.conversation_history[conv_id]
        assert len(history) == 4
        assert history[2].content == "Second message"
        assert history[3].content == "First response"  # Mock returns same response

    async def test_conversation_history_limit(self, service):
        """Test conversation history respects max_history_messages limit."""
        conv_id = "test_conv_limit"

        # Create service with small history limit for testing
        service.max_history_messages = 4  # System + 3 messages

        mock_completion = ChatCompletion(
            id="chatcmpl-123",
            object="chat.completion",
            created=1677652288,
            model="gpt-4",
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(role="assistant", content="Response"),
                    finish_reason="stop",
                )
            ],
            usage={"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
        )

        service.client.chat.completions.create = AsyncMock(return_value=mock_completion)

        # Add several messages to exceed limit
        for i in range(5):
            request = ChatRequest(
                message=f"Message {i}", user_id="user_123", conversation_id=conv_id
            )
            await service.generate_response(request)

        # Verify history was trimmed
        history = service.conversation_history[conv_id]
        assert len(history) <= service.max_history_messages

        # Verify most recent messages are kept
        assert history[-1].content == "Response"
        assert history[-2].content == "Message 4"

    async def test_clear_conversation_history(self, service):
        """Test clearing conversation history."""
        conv_id = "test_conv_clear"

        # Add some history
        service.conversation_history[conv_id] = [
            ChatMessage(content="Test", role="user"),
            ChatMessage(content="Response", role="assistant"),
        ]

        # Clear history
        service.clear_conversation_history(conv_id)

        # Verify history was cleared
        assert conv_id not in service.conversation_history

    async def test_get_conversation_summary(self, service):
        """Test getting conversation summary."""
        conv_id = "test_conv_summary"

        # Add conversation history
        service.conversation_history[conv_id] = [
            ChatMessage(content="Hello", role="user"),
            ChatMessage(content="Hi there!", role="assistant"),
            ChatMessage(content="How are you?", role="user"),
            ChatMessage(content="I'm doing well!", role="assistant"),
        ]

        summary = service.get_conversation_summary(conv_id)

        assert summary.conversation_id == conv_id
        assert summary.message_count == 4
        assert summary.last_message_time is not None
        assert "Hello" in summary.preview

    async def test_get_conversation_summary_nonexistent(self, service):
        """Test getting summary for non-existent conversation."""
        summary = service.get_conversation_summary("nonexistent")

        assert summary.conversation_id == "nonexistent"
        assert summary.message_count == 0
        assert summary.preview == "No messages yet"


class TestAzureOpenAIServiceStreaming:
    """Test streaming functionality of AzureOpenAIService."""

    @pytest.fixture
    def service(self, test_settings):
        """Create service for streaming tests."""
        return AzureOpenAIService(test_settings)

    @pytest.fixture
    def streaming_request(self):
        """Create a streaming chat request."""
        return ChatRequest(
            message="Tell me about AI careers", user_id="user_123", stream=True
        )

    async def test_generate_streaming_response_success(
        self, service, streaming_request, mock_streaming_response
    ):
        """Test successful streaming response generation."""
        service.client.chat.completions.create = AsyncMock(
            return_value=mock_streaming_response
        )

        chunks = []
        async for chunk in service.generate_streaming_response(streaming_request):
            chunks.append(chunk)

        # Verify chunks
        assert len(chunks) > 0
        assert chunks[0].conversation_id == streaming_request.conversation_id
        assert any(chunk.is_final for chunk in chunks)

        # Verify stream parameter was used
        call_args = service.client.chat.completions.create.call_args
        assert call_args[1]["stream"] is True

    async def test_streaming_error_handling(self, service, streaming_request):
        """Test error handling in streaming mode."""
        service.client.chat.completions.create = AsyncMock(
            side_effect=APIError("Streaming error")
        )

        with pytest.raises(APIError):
            async for chunk in service.generate_streaming_response(streaming_request):
                pass  # Should raise before yielding any chunks

    async def test_streaming_conversation_history_update(
        self, service, streaming_request, mock_streaming_response
    ):
        """Test that streaming responses update conversation history."""
        service.client.chat.completions.create = AsyncMock(
            return_value=mock_streaming_response
        )

        # Process streaming response
        full_content = ""
        async for chunk in service.generate_streaming_response(streaming_request):
            if not chunk.is_final:
                full_content += chunk.content

        # Verify conversation history was updated
        conv_id = streaming_request.conversation_id
        if conv_id:
            assert conv_id in service.conversation_history
            history = service.conversation_history[conv_id]
            assert len(history) >= 2  # User message + assistant response
            assert history[-1].role == "assistant"


class TestAzureOpenAIServiceEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def service(self, test_settings):
        """Create service for edge case tests."""
        return AzureOpenAIService(test_settings)

    async def test_empty_message_handling(self, service):
        """Test handling of requests with empty messages."""
        # This should be caught by Pydantic validation before reaching the service
        with pytest.raises(Exception):  # ValidationError from Pydantic
            ChatRequest(message="", user_id="user_123")

    async def test_very_long_conversation_history(self, service):
        """Test handling of very long conversation histories."""
        conv_id = "long_conv"

        # Create a very long conversation history
        long_history = []
        for i in range(100):
            long_history.extend(
                [
                    ChatMessage(content=f"User message {i}", role="user"),
                    ChatMessage(content=f"Assistant response {i}", role="assistant"),
                ]
            )

        service.conversation_history[conv_id] = long_history

        # Make a request
        request = ChatRequest(
            message="New message", user_id="user_123", conversation_id=conv_id
        )

        mock_completion = ChatCompletion(
            id="chatcmpl-123",
            object="chat.completion",
            created=1677652288,
            model="gpt-4",
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(role="assistant", content="Response"),
                    finish_reason="stop",
                )
            ],
            usage={"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
        )

        service.client.chat.completions.create = AsyncMock(return_value=mock_completion)

        # Should handle long history gracefully
        response = await service.generate_response(request)
        assert response.message == "Response"

        # Verify history was trimmed
        final_history = service.conversation_history[conv_id]
        assert len(final_history) <= service.max_history_messages

    async def test_concurrent_requests_same_conversation(self, service):
        """Test handling concurrent requests for the same conversation."""
        conv_id = "concurrent_conv"

        mock_completion = ChatCompletion(
            id="chatcmpl-123",
            object="chat.completion",
            created=1677652288,
            model="gpt-4",
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(
                        role="assistant", content="Concurrent response"
                    ),
                    finish_reason="stop",
                )
            ],
            usage={"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
        )

        service.client.chat.completions.create = AsyncMock(return_value=mock_completion)

        # Create multiple concurrent requests
        requests = [
            ChatRequest(
                message=f"Message {i}", user_id="user_123", conversation_id=conv_id
            )
            for i in range(3)
        ]

        # Execute concurrently
        responses = await asyncio.gather(
            *[service.generate_response(req) for req in requests]
        )

        # All should succeed
        assert len(responses) == 3
        assert all(r.message == "Concurrent response" for r in responses)

        # Conversation history should contain all messages
        history = service.conversation_history[conv_id]
        assert len(history) >= 6  # 3 user messages + 3 assistant responses
