"""
RAG-enhanced AI service for the AI Career Mentor Chatbot.

This service combines the existing Azure OpenAI capabilities with
Retrieval-Augmented Generation (RAG) using Azure Cognitive Search.
Demonstrates advanced AI engineering patterns for knowledge-enhanced responses.
"""

import logging
import time
from typing import List, Optional, AsyncGenerator, Dict, Any

from openai import AsyncAzureOpenAI
from openai._exceptions import APIError, RateLimitError, APITimeoutError

from src.config.settings import Settings
from src.models.chat_models import ChatMessage, ChatRequest
from src.models.rag_models import SearchQuery, SearchResult, RAGResponse
from src.services.search_service import AzureCognitiveSearchService

logger = logging.getLogger(__name__)


class RAGEnhancedAIService:
    """
    AI service with Retrieval-Augmented Generation capabilities.

    Enhances the basic AI service with knowledge retrieval from Azure Cognitive Search,
    providing more accurate and contextual responses based on the knowledge base.
    """

    def __init__(self, settings: Settings):
        """Initialize the RAG-enhanced AI service."""
        self.settings = settings

        # Initialize OpenAI client
        self.client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
        )

        # Initialize search service
        self.search_service = AzureCognitiveSearchService(settings)

        # Conversation history management
        self.conversation_history: Dict[str, List[ChatMessage]] = {}
        self.max_history_messages = 20

        # RAG configuration
        self.min_retrieval_score = 0.7
        self.max_retrieved_docs = 5
        self.enable_rag_for_query_types = [
            "career",
            "skill",
            "interview",
            "salary",
            "learning",
            "transition",
        ]

    async def initialize(self) -> bool:
        """
        Initialize the RAG service components.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Initialize search index
            index_created = await self.search_service.initialize_index()
            if not index_created:
                logger.warning(
                    "Search index initialization failed, RAG features may be limited"
                )

            logger.info("RAG-enhanced AI service initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            return False

    def _should_use_rag(
        self, query: str, conversation_context: Optional[str] = None
    ) -> bool:
        """
        Determine if RAG should be used for this query.

        Args:
            query: User's query
            conversation_context: Recent conversation context

        Returns:
            True if RAG should be used, False otherwise
        """
        query_lower = query.lower()

        # Check for career-related keywords
        career_keywords = [
            "career",
            "job",
            "skill",
            "interview",
            "salary",
            "learning",
            "transition",
            "ai engineer",
            "machine learning",
            "data science",
            "resume",
            "portfolio",
            "experience",
            "qualification",
            "certification",
            "bootcamp",
            "degree",
            "course",
            "training",
            "mentor",
            "advice",
        ]

        return any(keyword in query_lower for keyword in career_keywords)

    def _build_rag_prompt(
        self,
        original_query: str,
        retrieved_sources: List[SearchResult],
        conversation_history: List[ChatMessage],
    ) -> str:
        """
        Build an enhanced prompt with retrieved knowledge.

        Args:
            original_query: User's original query
            retrieved_sources: Retrieved knowledge sources
            conversation_history: Recent conversation messages

        Returns:
            Enhanced prompt with context
        """
        # Base system prompt
        system_prompt = """You are an expert AI Career Mentor with access to comprehensive career guidance knowledge. 
Your role is to provide personalized, actionable advice for professionals transitioning to or advancing in AI engineering roles.

Guidelines:
- Use the provided knowledge sources to enhance your responses
- Always cite sources when using specific information
- Provide practical, actionable advice
- Be encouraging but realistic about career challenges
- Tailor advice to the user's background and goals
- If knowledge sources don't contain relevant information, rely on your general expertise"""

        # Add retrieved knowledge context
        knowledge_context = ""
        if retrieved_sources:
            knowledge_context = "\n\nRELEVANT KNOWLEDGE SOURCES:\n"
            for i, source in enumerate(retrieved_sources, 1):
                knowledge_context += f"\n[Source {i}] {source.title}\n"
                knowledge_context += f"Type: {source.document_type.value}\n"
                knowledge_context += f"Summary: {source.summary}\n"
                knowledge_context += f"Content: {source.content_snippet}\n"
                if source.tags:
                    knowledge_context += f"Tags: {', '.join(source.tags)}\n"
                knowledge_context += f"Relevance Score: {source.similarity_score:.2f}\n"

        # Add conversation context
        context_prompt = ""
        if conversation_history:
            context_prompt = "\n\nCONVERSATION CONTEXT:\n"
            for msg in conversation_history[-6:]:  # Last 6 messages for context
                context_prompt += f"{msg.role.title()}: {msg.content}\n"

        # Combine all parts
        enhanced_prompt = f"{system_prompt}{knowledge_context}{context_prompt}\n\nUSER QUERY: {original_query}\n\nPlease provide a comprehensive response using the knowledge sources where relevant, and cite them appropriately."

        return enhanced_prompt

    async def generate_rag_response(self, request: ChatRequest) -> RAGResponse:
        """
        Generate a RAG-enhanced response to the user's query.

        Args:
            request: Chat request with user's message

        Returns:
            RAG-enhanced response with sources and metadata
        """
        start_time = time.time()
        retrieval_time = 0
        generation_time = 0
        retrieved_sources = []

        try:
            # Get conversation history
            conversation_history = []
            if request.conversation_id:
                conversation_history = self.conversation_history.get(
                    request.conversation_id, []
                )

            # Determine if we should use RAG
            use_rag = self._should_use_rag(request.message)

            if use_rag:
                # Perform knowledge retrieval
                retrieval_start = time.time()

                # Build search query with conversation context
                context = ""
                if conversation_history:
                    recent_messages = conversation_history[
                        -4:
                    ]  # Last 4 messages for context
                    context = " ".join([msg.content for msg in recent_messages])

                search_query = SearchQuery(
                    query=request.message,
                    conversation_context=context,
                    max_results=self.max_retrieved_docs,
                    similarity_threshold=self.min_retrieval_score,
                )

                retrieved_sources = await self.search_service.semantic_search(
                    search_query
                )
                retrieval_time = int((time.time() - retrieval_start) * 1000)

                logger.info(f"Retrieved {len(retrieved_sources)} sources for query")

            # Generate response
            generation_start = time.time()

            if retrieved_sources:
                # Use RAG-enhanced prompt
                enhanced_prompt = self._build_rag_prompt(
                    request.message, retrieved_sources, conversation_history
                )
                messages = [{"role": "system", "content": enhanced_prompt}]
            else:
                # Use standard conversation flow
                messages = [
                    {
                        "role": "system",
                        "content": """You are an expert AI Career Mentor specializing in helping professionals 
                        transition to and advance in AI engineering roles. Provide practical, actionable advice 
                        tailored to each person's background and goals.""",
                    }
                ]

                # Add conversation history
                for msg in conversation_history[-10:]:  # Last 10 messages
                    messages.append({"role": msg.role, "content": msg.content})

                # Add current message
                messages.append({"role": "user", "content": request.message})

            # Call OpenAI API
            completion = await self.client.chat.completions.create(
                model=self.settings.azure_openai_deployment_name,
                messages=messages,
                temperature=request.temperature or self.settings.default_temperature,
                max_tokens=request.max_tokens or self.settings.max_tokens,
                stream=False,
            )

            generation_time = int((time.time() - generation_start) * 1000)

            # Extract response
            response_message = completion.choices[0].message.content

            # Calculate confidence score based on retrieval quality
            confidence_score = None
            if retrieved_sources:
                avg_similarity = sum(
                    s.similarity_score for s in retrieved_sources
                ) / len(retrieved_sources)
                confidence_score = min(
                    0.95, 0.7 + (avg_similarity * 0.25)
                )  # Scale to 0.7-0.95

            # Update conversation history
            if request.conversation_id:
                if request.conversation_id not in self.conversation_history:
                    self.conversation_history[request.conversation_id] = []

                history = self.conversation_history[request.conversation_id]

                # Add user message
                history.append(ChatMessage(content=request.message, role="user"))

                # Add assistant response
                history.append(ChatMessage(content=response_message, role="assistant"))

                # Trim history if too long
                if len(history) > self.max_history_messages:
                    self.conversation_history[request.conversation_id] = history[
                        -self.max_history_messages :
                    ]

            # Create RAG response
            total_time = int((time.time() - start_time) * 1000)

            rag_response = RAGResponse(
                message=response_message,
                conversation_id=request.conversation_id,
                ai_model=completion.model,
                retrieved_sources=retrieved_sources,
                retrieval_query=request.message if retrieved_sources else None,
                confidence_score=confidence_score,
                knowledge_enhanced=len(retrieved_sources) > 0,
                processing_time_ms=total_time,
                retrieval_time_ms=retrieval_time if retrieval_time > 0 else None,
                generation_time_ms=generation_time,
                token_usage={
                    "prompt_tokens": completion.usage.prompt_tokens,
                    "completion_tokens": completion.usage.completion_tokens,
                    "total_tokens": completion.usage.total_tokens,
                }
                if completion.usage
                else None,
            )

            logger.info(
                f"Generated RAG response in {total_time}ms "
                f"(retrieval: {retrieval_time}ms, generation: {generation_time}ms)"
            )

            return rag_response

        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise
        except APITimeoutError as e:
            logger.error(f"API timeout: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in RAG response generation: {e}")
            raise

    async def generate_streaming_rag_response(
        self, request: ChatRequest
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate a streaming RAG-enhanced response.

        Args:
            request: Chat request with streaming enabled

        Yields:
            Dictionary chunks with response data and metadata
        """
        start_time = time.time()
        retrieval_time = 0
        retrieved_sources = []

        try:
            # Perform retrieval first (if applicable)
            use_rag = self._should_use_rag(request.message)

            if use_rag:
                retrieval_start = time.time()

                conversation_history = []
                if request.conversation_id:
                    conversation_history = self.conversation_history.get(
                        request.conversation_id, []
                    )

                context = ""
                if conversation_history:
                    recent_messages = conversation_history[-4:]
                    context = " ".join([msg.content for msg in recent_messages])

                search_query = SearchQuery(
                    query=request.message,
                    conversation_context=context,
                    max_results=self.max_retrieved_docs,
                    similarity_threshold=self.min_retrieval_score,
                )

                retrieved_sources = await self.search_service.semantic_search(
                    search_query
                )
                retrieval_time = int((time.time() - retrieval_start) * 1000)

                # Yield retrieval metadata
                yield {
                    "type": "retrieval_complete",
                    "retrieved_sources": [
                        {
                            "title": source.title,
                            "document_type": source.document_type.value,
                            "similarity_score": source.similarity_score,
                        }
                        for source in retrieved_sources
                    ],
                    "retrieval_time_ms": retrieval_time,
                }

            # Build messages for streaming
            conversation_history = []
            if request.conversation_id:
                conversation_history = self.conversation_history.get(
                    request.conversation_id, []
                )

            if retrieved_sources:
                enhanced_prompt = self._build_rag_prompt(
                    request.message, retrieved_sources, conversation_history
                )
                messages = [{"role": "system", "content": enhanced_prompt}]
            else:
                messages = [
                    {
                        "role": "system",
                        "content": "You are an expert AI Career Mentor. Provide practical, actionable advice.",
                    }
                ]

                for msg in conversation_history[-10:]:
                    messages.append({"role": msg.role, "content": msg.content})

                messages.append({"role": "user", "content": request.message})

            # Stream response
            full_response = ""
            async for chunk in await self.client.chat.completions.create(
                model=self.settings.azure_openai_deployment_name,
                messages=messages,
                temperature=request.temperature or self.settings.default_temperature,
                max_tokens=request.max_tokens or self.settings.max_tokens,
                stream=True,
            ):
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content

                    yield {
                        "type": "content_chunk",
                        "content": content,
                        "conversation_id": request.conversation_id,
                    }

            # Final metadata
            total_time = int((time.time() - start_time) * 1000)

            # Update conversation history
            if request.conversation_id:
                if request.conversation_id not in self.conversation_history:
                    self.conversation_history[request.conversation_id] = []

                history = self.conversation_history[request.conversation_id]
                history.append(ChatMessage(content=request.message, role="user"))
                history.append(ChatMessage(content=full_response, role="assistant"))

                if len(history) > self.max_history_messages:
                    self.conversation_history[request.conversation_id] = history[
                        -self.max_history_messages :
                    ]

            yield {
                "type": "response_complete",
                "conversation_id": request.conversation_id,
                "knowledge_enhanced": len(retrieved_sources) > 0,
                "processing_time_ms": total_time,
                "retrieval_time_ms": retrieval_time if retrieval_time > 0 else None,
            }

        except Exception as e:
            logger.error(f"Error in streaming RAG response: {e}")
            yield {"type": "error", "error": str(e)}

    def clear_conversation_history(self, conversation_id: str):
        """Clear conversation history for a specific conversation."""
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]
            logger.info(f"Cleared conversation history for: {conversation_id}")

    async def get_knowledge_stats(self):
        """Get knowledge base statistics."""
        return await self.search_service.get_knowledge_base_stats()

    async def close(self):
        """Close all service connections."""
        try:
            await self.client.close()
            await self.search_service.close()
            logger.info("RAG-enhanced AI service closed successfully")
        except Exception as e:
            logger.error(f"Error closing RAG service: {e}")
