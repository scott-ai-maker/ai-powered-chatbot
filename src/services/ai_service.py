"""
Azure OpenAI Service for the AI Career Mentor Chatbot.

This service provides async integration with Azure OpenAI, implementing
enterprise-grade patterns for authentication, error handling, retry logic,
and streaming responses.
"""

import asyncio
import time
from typing import AsyncGenerator, Dict, List, Optional, Literal, cast
from datetime import datetime

import httpx
import structlog
from openai import AsyncAzureOpenAI
from openai.types.chat import ChatCompletionMessageParam
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.config.settings import Settings
from src.models.chat_models import ChatMessage, ChatResponse, StreamingChatChunk


logger = structlog.get_logger()


class AzureOpenAIService:
    """
    Production-ready Azure OpenAI service with async patterns.

    Features:
    - Async HTTP client for non-blocking operations
    - Automatic retry with exponential backoff
    - Streaming response support
    - Conversation context management
    - Token usage tracking
    - Comprehensive error handling
    - Career mentoring system prompts
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client: Optional[AsyncAzureOpenAI] = None
        self._conversation_contexts: Dict[str, List[ChatMessage]] = {}

        # Rate limiting
        self._semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests

        # Career mentoring system prompt
        self.system_prompt = """You are an expert AI Career Mentor specializing in helping people transition into AI engineering roles. You have deep knowledge of:

- AI/ML engineering career paths and requirements
- Technical skills needed (Python, ML frameworks, cloud platforms)
- Educational pathways (courses, certifications, degrees)
- Portfolio project recommendations
- Interview preparation and common questions
- Industry trends and job market insights
- Salary expectations and negotiation
- Networking and professional development

Provide practical, actionable advice that's specific to the user's background and goals. Be encouraging but realistic about the challenges and timeline for career transitions. Focus on concrete next steps they can take."""

    async def __aenter__(self):
        """Async context manager entry - initialize Azure OpenAI client."""
        try:
            self.client = AsyncAzureOpenAI(
                api_key=self.settings.azure_openai_key,
                api_version=self.settings.azure_openai_api_version,
                azure_endpoint=self.settings.azure_openai_endpoint,
                timeout=httpx.Timeout(60.0),  # 60 second timeout
                max_retries=3,
            )

            logger.info(
                "Azure OpenAI client initialized",
                endpoint=self.settings.azure_openai_endpoint,
                api_version=self.settings.azure_openai_api_version,
                deployment=self.settings.azure_openai_deployment_name,
            )

            return self

        except Exception as e:
            logger.error("Failed to initialize Azure OpenAI client", error=str(e))
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup resources."""
        if self.client:
            await self.client.close()
            logger.info("Azure OpenAI client closed")

    async def health_check(self) -> bool:
        """Check if Azure OpenAI service is accessible."""
        try:
            if self.client is None:
                return False
            # Simple test request
            response = await self.client.chat.completions.create(
                model=self.settings.azure_openai_deployment_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5,
                temperature=0.1,
            )
            return bool(response.choices and response.choices[0].message.content)

        except Exception as e:
            logger.warning("Azure OpenAI health check failed", error=str(e))
            return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, asyncio.TimeoutError)),
    )
    async def generate_response(
        self,
        message: str,
        conversation_id: str,
        user_id: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ChatResponse:
        """
        Generate AI response with retry logic and context management.

        Args:
            message: User message
            conversation_id: Conversation identifier for context
            user_id: User identifier
            temperature: Response creativity (overrides default)
            max_tokens: Maximum tokens (overrides default)

        Returns:
            ChatResponse with AI-generated content and metadata
        """
        start_time = time.time()

        async with self._semaphore:  # Rate limiting
            try:
                # Build conversation context
                messages = self._build_conversation_context(
                    conversation_id, message, user_id
                )

                # Use provided parameters or defaults from settings
                temperature = temperature or self.settings.default_temperature
                max_tokens = max_tokens or self.settings.max_tokens

                logger.info(
                    "Generating AI response",
                    conversation_id=conversation_id,
                    user_id=user_id,
                    message_length=len(message),
                    context_messages=len(messages),
                )

                # Call Azure OpenAI
                if self.client is None:
                    raise RuntimeError("Azure OpenAI client not initialized")
                response = await self.client.chat.completions.create(
                    model=self.settings.azure_openai_deployment_name,
                    messages=cast(List[ChatCompletionMessageParam], messages),
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=0.95,
                    frequency_penalty=0.2,
                    presence_penalty=0.1,
                )

                processing_time = int((time.time() - start_time) * 1000)

                # Extract response content
                ai_message = response.choices[0].message.content
                if not ai_message:
                    raise ValueError("Empty response from Azure OpenAI")

                # Update conversation context
                self._update_conversation_context(
                    conversation_id, message, ai_message, user_id
                )

                # Determine response type based on content
                response_type = self._classify_response(ai_message)

                logger.info(
                    "AI response generated successfully",
                    conversation_id=conversation_id,
                    processing_time_ms=processing_time,
                    response_length=len(ai_message),
                    response_type=response_type,
                )

                return ChatResponse(
                    message=ai_message,
                    conversation_id=conversation_id,
                    ai_model=self.settings.azure_openai_deployment_name,
                    processing_time_ms=processing_time,
                    token_usage={
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    }
                    if response.usage
                    else None,
                    confidence_score=self._calculate_confidence_score(response),
                    response_type=response_type,
                )

            except Exception as e:
                processing_time = int((time.time() - start_time) * 1000)
                logger.error(
                    "Failed to generate AI response",
                    conversation_id=conversation_id,
                    error=str(e),
                    error_type=type(e).__name__,
                    processing_time_ms=processing_time,
                )
                raise

    async def generate_streaming_response(
        self,
        message: str,
        conversation_id: str,
        user_id: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[StreamingChatChunk, None]:
        """
        Generate streaming AI response for real-time chat experience.

        This provides the ChatGPT-like streaming experience where users
        see the response being generated token by token.
        """
        async with self._semaphore:
            try:
                messages = self._build_conversation_context(
                    conversation_id, message, user_id
                )

                temperature = temperature or self.settings.default_temperature
                max_tokens = max_tokens or self.settings.max_tokens

                logger.info(
                    "Starting streaming AI response",
                    conversation_id=conversation_id,
                    user_id=user_id,
                )

                # Create streaming completion
                if self.client is None:
                    raise RuntimeError("Azure OpenAI client not initialized")
                stream = await self.client.chat.completions.create(
                    model=self.settings.azure_openai_deployment_name,
                    messages=cast(List[ChatCompletionMessageParam], messages),
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                    top_p=0.95,
                    frequency_penalty=0.2,
                    presence_penalty=0.1,
                )

                full_response = ""
                chunk_count = 0

                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        chunk_count += 1

                        yield StreamingChatChunk(
                            id=f"chunk_{chunk_count:03d}",
                            conversation_id=conversation_id,
                            content=content,
                            is_final=False,
                        )

                # Send final chunk
                yield StreamingChatChunk(
                    id="chunk_final",
                    conversation_id=conversation_id,
                    content="",
                    is_final=True,
                )

                # Update conversation context with complete response
                self._update_conversation_context(
                    conversation_id, message, full_response, user_id
                )

                logger.info(
                    "Streaming response completed",
                    conversation_id=conversation_id,
                    chunks_sent=chunk_count,
                    total_length=len(full_response),
                )

            except Exception as e:
                logger.error(
                    "Streaming response failed",
                    conversation_id=conversation_id,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                # Send error chunk
                yield StreamingChatChunk(
                    id="chunk_error",
                    conversation_id=conversation_id,
                    content=f"Error: {str(e)}",
                    is_final=True,
                )

    def _build_conversation_context(
        self, conversation_id: str, current_message: str, user_id: str
    ) -> List[Dict[str, str]]:
        """Build conversation context for AI model."""
        messages = [{"role": "system", "content": self.system_prompt}]

        # Add conversation history (last N messages)
        if conversation_id in self._conversation_contexts:
            history = self._conversation_contexts[conversation_id]
            # Keep last 10 messages for context (5 user + 5 assistant)
            recent_history = history[-10:] if len(history) > 10 else history

            for msg in recent_history:
                messages.append({"role": msg.role, "content": msg.content})

        # Add current user message
        messages.append({"role": "user", "content": current_message})

        return messages

    def _update_conversation_context(
        self, conversation_id: str, user_message: str, ai_response: str, user_id: str
    ):
        """Update conversation context with new messages."""
        if conversation_id not in self._conversation_contexts:
            self._conversation_contexts[conversation_id] = []

        context = self._conversation_contexts[conversation_id]

        # Add user message
        context.append(
            ChatMessage(content=user_message, role="user", timestamp=datetime.utcnow())
        )

        # Add AI response
        context.append(
            ChatMessage(
                content=ai_response, role="assistant", timestamp=datetime.utcnow()
            )
        )

        # Keep context manageable (use configured max history)
        max_history = self.settings.max_conversation_history
        if len(context) > max_history:
            self._conversation_contexts[conversation_id] = context[-max_history:]

    def _classify_response(
        self, response_content: str
    ) -> Literal["career_advice", "general", "clarification"]:
        """Classify the type of response based on content."""
        content_lower = response_content.lower()

        career_keywords = [
            "career",
            "job",
            "role",
            "engineer",
            "transition",
            "skills",
            "interview",
            "resume",
            "portfolio",
            "salary",
            "experience",
        ]

        if any(keyword in content_lower for keyword in career_keywords):
            return "career_advice"
        elif "?" in response_content or "clarify" in content_lower:
            return "clarification"
        else:
            return "general"

    def _calculate_confidence_score(self, response) -> float:
        """Calculate confidence score based on response metadata."""
        # Simple heuristic - in production, you might use more sophisticated methods
        if response.choices and response.choices[0].finish_reason == "stop":
            return 0.9  # High confidence for complete responses
        elif response.choices and response.choices[0].finish_reason == "length":
            return 0.7  # Medium confidence if truncated
        else:
            return 0.5  # Lower confidence for other cases

    def clear_conversation_context(self, conversation_id: str):
        """Clear conversation context for a specific conversation."""
        if conversation_id in self._conversation_contexts:
            del self._conversation_contexts[conversation_id]
            logger.info("Conversation context cleared", conversation_id=conversation_id)

    def get_conversation_summary(self, conversation_id: str) -> Optional[dict]:
        """Get summary statistics for a conversation."""
        if conversation_id not in self._conversation_contexts:
            return None

        context = self._conversation_contexts[conversation_id]
        user_messages = [msg for msg in context if msg.role == "user"]
        assistant_messages = [msg for msg in context if msg.role == "assistant"]

        return {
            "conversation_id": conversation_id,
            "total_messages": len(context),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "first_message_time": context[0].timestamp.isoformat() if context else None,
            "last_message_time": context[-1].timestamp.isoformat() if context else None,
        }
