"""
Chat endpoints for the AI Career Mentor Chatbot.

These endpoints provide the core chat functionality with both
regular and streaming response options, enhanced with RAG capabilities
for knowledge-augmented responses. Demonstrates production-ready API 
design with proper validation, error handling, and async patterns.
"""

import uuid
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
import structlog

from src.config.settings import Settings, get_settings_dependency
from src.models.chat_models import (
    ChatRequest, 
    ChatResponse, 
    StreamingChatChunk,
    ErrorResponse,
    ConversationSummary
)
from src.models.rag_models import RAGResponse, SearchQuery
from src.services.ai_service import AzureOpenAIService
from src.services.rag_service import RAGEnhancedAIService
from src.services.search_service import AzureCognitiveSearchService
from src.services.monitoring_service import get_monitoring_service
from src.services.monitoring_middleware import ChatMetricsCollector


logger = structlog.get_logger()
router = APIRouter()


# Global service instances (will be properly managed in main.py)
_ai_service: AzureOpenAIService = None
_rag_service: RAGEnhancedAIService = None
_search_service: AzureCognitiveSearchService = None


async def get_ai_service(
    settings: Settings = Depends(get_settings_dependency)
) -> AzureOpenAIService:
    """Dependency to get AI service instance."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AzureOpenAIService(settings)
        await _ai_service.__aenter__()
    return _ai_service


async def get_rag_service(
    settings: Settings = Depends(get_settings_dependency)
) -> RAGEnhancedAIService:
    """Dependency to get RAG service instance."""
    global _rag_service, _search_service
    if _rag_service is None:
        # Initialize search service first
        _search_service = AzureCognitiveSearchService(settings)
        await _search_service.initialize_index()
        
        # Initialize RAG service
        _rag_service = RAGEnhancedAIService(
            settings=settings,
            search_service=_search_service
        )
    return _rag_service


@router.post("/chat", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    use_rag: bool = Query(False, description="Enable RAG (knowledge-enhanced) responses"),
    ai_service: AzureOpenAIService = Depends(get_ai_service),
    rag_service: RAGEnhancedAIService = Depends(get_rag_service)
) -> ChatResponse:
    """
    Generate AI response for a chat message with optional RAG enhancement.
    
    This endpoint provides the core chat functionality:
    - Validates input using Pydantic models
    - Generates contextual AI responses
    - Optional knowledge-enhanced responses via RAG
    - Tracks conversation history
    - Returns structured response with metadata
    
    Perfect for traditional request-response chat interfaces.
    """
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        logger.info(
            "Processing chat request",
            user_id=request.user_id,
            conversation_id=conversation_id,
            message_length=len(request.message),
            use_rag=use_rag,
            stream=request.stream
        )
        
        if use_rag:
            # Use RAG-enhanced response
            rag_response = await rag_service.generate_rag_response(
                message=request.message,
                conversation_id=conversation_id,
                user_id=request.user_id,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            # Convert RAG response to ChatResponse format
            response = ChatResponse(
                message=rag_response.response,
                conversation_id=conversation_id,
                response_type="rag_enhanced",
                processing_time_ms=rag_response.processing_time_ms,
                metadata={
                    "ai_model": rag_response.ai_model,
                    "sources_used": len(rag_response.sources),
                    "rag_confidence": rag_response.confidence_score,
                    "knowledge_sources": [
                        {
                            "title": source.title,
                            "confidence": source.confidence_score,
                            "document_type": source.document_type
                        }
                        for source in rag_response.sources[:3]  # Top 3 sources
                    ]
                }
            )
        else:
            # Use standard AI response
            response = await ai_service.generate_response(
                message=request.message,
                conversation_id=conversation_id,
                user_id=request.user_id,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        
        logger.info(
            "Chat response generated",
            conversation_id=conversation_id,
            processing_time_ms=response.processing_time_ms,
            response_type=response.response_type,
            use_rag=use_rag
        )
        
        return response
        
    except ValueError as e:
        logger.warning("Invalid chat request", error=str(e), user_id=request.user_id)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(
            "Chat completion failed",
            error=str(e),
            error_type=type(e).__name__,
            user_id=request.user_id,
            use_rag=use_rag
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to generate response. Please try again."
        )


@router.post("/chat/rag", response_model=RAGResponse)
async def rag_chat_completion(
    request: ChatRequest,
    rag_service: RAGEnhancedAIService = Depends(get_rag_service)
) -> RAGResponse:
    """
    Generate knowledge-enhanced AI response using RAG.
    
    This endpoint specifically uses Retrieval-Augmented Generation to:
    - Search the knowledge base for relevant information
    - Combine retrieved knowledge with the user's question
    - Generate responses that are grounded in factual information
    - Provide source citations and confidence scores
    
    Ideal for career guidance questions that benefit from specific expertise.
    """
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        logger.info(
            "Processing RAG chat request",
            user_id=request.user_id,
            conversation_id=conversation_id,
            message_length=len(request.message)
        )
        
        # Generate RAG-enhanced response
        response = await rag_service.generate_rag_response(
            message=request.message,
            conversation_id=conversation_id,
            user_id=request.user_id,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        logger.info(
            "RAG response generated",
            conversation_id=conversation_id,
            processing_time_ms=response.processing_time_ms,
            sources_count=len(response.sources),
            confidence_score=response.confidence_score
        )
        
        return response
        
    except ValueError as e:
        logger.warning("Invalid RAG request", error=str(e), user_id=request.user_id)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(
            "RAG completion failed",
            error=str(e),
            error_type=type(e).__name__,
            user_id=request.user_id
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to generate knowledge-enhanced response. Please try again."
        )


@router.post("/chat/stream")
async def chat_completion_stream(
    request: ChatRequest,
    ai_service: AzureOpenAIService = Depends(get_ai_service)
):
    """
    Generate streaming AI response for real-time chat experience.
    
    This endpoint provides ChatGPT-like streaming where users see
    the response being generated token by token. This creates a
    much more engaging user experience.
    
    Returns Server-Sent Events (SSE) compatible stream.
    """
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        logger.info(
            "Processing streaming chat request",
            user_id=request.user_id,
            conversation_id=conversation_id,
            message_length=len(request.message)
        )
        
        async def generate_stream():
            """Generate streaming response."""
            try:
                async for chunk in ai_service.generate_streaming_response(
                    message=request.message,
                    conversation_id=conversation_id,
                    user_id=request.user_id,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                ):
                    # Format as Server-Sent Events
                    chunk_json = chunk.model_dump_json()
                    yield f"data: {chunk_json}\n\n"
                    
                    if chunk.is_final:
                        break
                        
            except Exception as e:
                logger.error("Streaming failed", error=str(e))
                error_chunk = StreamingChatChunk(
                    id="error",
                    conversation_id=conversation_id,
                    content=f"Error: {str(e)}",
                    is_final=True
                )
                yield f"data: {error_chunk.model_dump_json()}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except Exception as e:
        logger.error("Streaming setup failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to initialize streaming response"
        )


@router.post("/chat/rag/stream")
async def rag_chat_completion_stream(
    request: ChatRequest,
    rag_service: RAGEnhancedAIService = Depends(get_rag_service)
):
    """
    Generate streaming knowledge-enhanced AI response using RAG.
    
    This endpoint combines the benefits of RAG with real-time streaming:
    - Searches knowledge base for relevant information
    - Streams the AI response as it's generated
    - Provides source citations in the final chunk
    - Creates engaging user experience with knowledge-grounded responses
    
    Returns Server-Sent Events (SSE) compatible stream with RAG metadata.
    """
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        logger.info(
            "Processing streaming RAG chat request",
            user_id=request.user_id,
            conversation_id=conversation_id,
            message_length=len(request.message)
        )
        
        async def generate_rag_stream():
            """Generate streaming RAG response."""
            try:
                async for chunk in rag_service.generate_streaming_rag_response(
                    message=request.message,
                    conversation_id=conversation_id,
                    user_id=request.user_id,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                ):
                    # Format as Server-Sent Events
                    chunk_json = chunk.model_dump_json()
                    yield f"data: {chunk_json}\n\n"
                    
                    if chunk.is_final:
                        break
                        
            except Exception as e:
                logger.error("RAG streaming failed", error=str(e))
                error_chunk = StreamingChatChunk(
                    id="error",
                    conversation_id=conversation_id,
                    content=f"Error: {str(e)}",
                    is_final=True
                )
                yield f"data: {error_chunk.model_dump_json()}\n\n"
        
        return StreamingResponse(
            generate_rag_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except Exception as e:
        logger.error("RAG streaming setup failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to initialize streaming RAG response"
        )


@router.post("/search")
async def search_knowledge_base(
    query: str = Query(..., description="Search query for the knowledge base"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results to return"),
    document_types: Optional[str] = Query(None, description="Comma-separated document types to filter"),
    min_confidence: float = Query(0.7, ge=0.0, le=1.0, description="Minimum confidence score for results"),
    search_service: AzureCognitiveSearchService = Depends(lambda: get_rag_service().search_service)
) -> Dict[str, Any]:
    """
    Search the knowledge base directly for relevant information.
    
    This endpoint allows direct access to the search functionality:
    - Semantic search across the knowledge base
    - Filter by document types and confidence scores
    - Get structured search results with metadata
    - Useful for building search interfaces or debugging RAG
    
    Perfect for exploring available knowledge without AI generation.
    """
    try:
        logger.info(
            "Processing knowledge base search",
            query=query,
            limit=limit,
            document_types=document_types,
            min_confidence=min_confidence
        )
        
        # Parse document types filter
        document_type_filter = None
        if document_types:
            document_type_filter = [dt.strip() for dt in document_types.split(",")]
        
        # Create search query
        search_query = SearchQuery(
            query=query,
            max_results=limit,
            min_confidence_score=min_confidence,
            document_types=document_type_filter
        )
        
        # Perform search
        search_results = await search_service.semantic_search(search_query)
        
        # Format response
        response = {
            "query": query,
            "total_results": len(search_results.results),
            "max_results": limit,
            "min_confidence": min_confidence,
            "document_types_filter": document_type_filter,
            "results": [
                {
                    "title": result.title,
                    "summary": result.summary,
                    "document_type": result.document_type,
                    "confidence_score": result.confidence_score,
                    "tags": result.tags,
                    "metadata": result.metadata
                }
                for result in search_results.results
            ],
            "processing_time_ms": search_results.processing_time_ms
        }
        
        logger.info(
            "Knowledge base search completed",
            query=query,
            results_count=len(search_results.results),
            processing_time_ms=search_results.processing_time_ms
        )
        
        return response
        
    except ValueError as e:
        logger.warning("Invalid search request", error=str(e), query=query)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid search request: {str(e)}"
        )
    except Exception as e:
        logger.error(
            "Knowledge base search failed",
            error=str(e),
            error_type=type(e).__name__,
            query=query
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to search knowledge base. Please try again."
        )


@router.get("/knowledge/stats")
async def get_knowledge_base_stats(
    search_service: AzureCognitiveSearchService = Depends(lambda: get_rag_service().search_service)
) -> Dict[str, Any]:
    """
    Get statistics about the knowledge base.
    
    Provides insights into:
    - Total number of documents
    - Document distribution by type
    - Index health and status
    - Last update information
    
    Useful for monitoring and administration.
    """
    try:
        logger.info("Retrieving knowledge base statistics")
        
        # Get knowledge base stats
        stats = await search_service.get_knowledge_base_stats()
        
        response = {
            "total_documents": stats.total_documents,
            "documents_by_type": stats.documents_by_type,
            "total_size_mb": stats.total_size_mb,
            "last_updated": stats.last_updated.isoformat() if stats.last_updated else None,
            "index_health": "healthy",  # Would implement actual health check
            "available_document_types": list(stats.documents_by_type.keys()) if stats.documents_by_type else []
        }
        
        logger.info(
            "Knowledge base statistics retrieved",
            total_documents=stats.total_documents,
            document_types=len(stats.documents_by_type) if stats.documents_by_type else 0
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Failed to get knowledge base statistics",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve knowledge base statistics"
        )


@router.get("/conversations/{conversation_id}/summary")
async def get_conversation_summary(
    conversation_id: str,
    ai_service: AzureOpenAIService = Depends(get_ai_service)
) -> Dict[str, Any]:
    """
    Get summary information for a conversation.
    
    Useful for conversation management, analytics, and
    providing users with conversation history overview.
    """
    try:
        summary = ai_service.get_conversation_summary(conversation_id)
        
        if summary is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get conversation summary",
            conversation_id=conversation_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve conversation summary"
        )


@router.delete("/conversations/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    background_tasks: BackgroundTasks,
    ai_service: AzureOpenAIService = Depends(get_ai_service)
) -> Dict[str, str]:
    """
    Clear conversation history.
    
    Allows users to start fresh conversations or clear
    sensitive information. Uses background tasks for
    non-blocking operation.
    """
    def clear_context():
        """Background task to clear conversation context."""
        ai_service.clear_conversation_context(conversation_id)
    
    background_tasks.add_task(clear_context)
    
    return {
        "message": f"Conversation {conversation_id} will be cleared",
        "status": "success"
    }


@router.get("/conversations/active")
async def get_active_conversations(
    ai_service: AzureOpenAIService = Depends(get_ai_service)
) -> Dict[str, Any]:
    """
    Get information about currently active conversations.
    
    Useful for monitoring, analytics, and resource management.
    In production, this might be restricted to admin users.
    """
    try:
        # Get active conversation count (simplified implementation)
        active_count = len(ai_service._conversation_contexts)
        
        return {
            "active_conversations": active_count,
            "timestamp": "2025-10-04T10:30:00Z",  # Would use real timestamp
            "status": "success"
        }
        
    except Exception as e:
        logger.error("Failed to get active conversations", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve conversation statistics"
        )