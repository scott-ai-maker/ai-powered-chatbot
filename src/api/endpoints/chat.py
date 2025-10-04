"""
Chat endpoints for the AI Career Mentor Chatbot.

These endpoints provide the core chat functionality with both
regular and streaming response options. They demonstrate
production-ready API design with proper validation,
error handling, and async patterns.
"""

import uuid
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
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
from src.services.ai_service import AzureOpenAIService


logger = structlog.get_logger()
router = APIRouter()


# Global AI service instance (will be properly managed in main.py)
_ai_service: AzureOpenAIService = None


async def get_ai_service(
    settings: Settings = Depends(get_settings_dependency)
) -> AzureOpenAIService:
    """Dependency to get AI service instance."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AzureOpenAIService(settings)
        await _ai_service.__aenter__()
    return _ai_service


@router.post("/chat", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    ai_service: AzureOpenAIService = Depends(get_ai_service)
) -> ChatResponse:
    """
    Generate AI response for a chat message.
    
    This endpoint provides the core chat functionality:
    - Validates input using Pydantic models
    - Generates contextual AI responses
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
            stream=request.stream
        )
        
        # Generate AI response
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
            response_type=response.response_type
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
            user_id=request.user_id
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to generate response. Please try again."
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