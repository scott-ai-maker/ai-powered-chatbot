"""
Chat-related Pydantic models for request/response validation.

These models ensure type safety and automatic validation for all
chat-related API operations. They follow OpenAPI standards and
provide excellent IDE support and documentation.
"""

from datetime import datetime
from typing import Dict, List, Optional, Literal, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    """A single chat message in a conversation."""
    
    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique message identifier")
    content: str = Field(..., min_length=1, max_length=4000, description="Message content")
    role: Literal["user", "assistant", "system"] = Field(..., description="Message role")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")


class ChatRequest(BaseModel):
    """Request model for chat completion."""
    
    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    user_id: str = Field(..., description="User identifier")
    stream: bool = Field(default=False, description="Whether to stream the response")
    
    # AI parameters (optional overrides)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Response creativity (0-2)")
    max_tokens: Optional[int] = Field(None, ge=1, le=4000, description="Maximum response tokens")
    
    @field_validator('message')
    @classmethod
    def validate_message_content(cls, v: str) -> str:
        """Ensure message is not just whitespace."""
        if not v.strip():
            raise ValueError('Message cannot be empty or just whitespace')
        return v.strip()


class ChatResponse(BaseModel):
    """Response model for chat completion."""
    
    id: str = Field(default_factory=lambda: str(uuid4()), description="Response identifier")
    message: str = Field(..., description="AI assistant response")
    conversation_id: str = Field(..., description="Conversation identifier")
    
    # Metadata
    ai_model: str = Field(..., description="AI model used for generation")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    token_usage: Optional[Dict[str, Any]] = Field(None, description="Token usage statistics")
    
    # Quality metrics
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Response confidence")
    response_type: Literal["career_advice", "general", "clarification"] = Field(
        default="career_advice", 
        description="Type of response provided"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "id": "resp_12345",
                "message": "To transition into AI engineering, I'd recommend starting with...",
                "conversation_id": "conv_67890",
                "ai_model": "gpt-4",
                "processing_time_ms": 1250,
                "confidence_score": 0.92,
                "response_type": "career_advice"
            }
        }


class ConversationSummary(BaseModel):
    """Summary of a conversation session."""
    
    conversation_id: str = Field(..., description="Conversation identifier")
    user_id: str = Field(..., description="User identifier")
    message_count: int = Field(..., ge=0, description="Number of messages")
    started_at: datetime = Field(..., description="Conversation start time")
    last_activity: datetime = Field(..., description="Last message timestamp")
    topics_discussed: List[str] = Field(default_factory=list, description="Main topics covered")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StreamingChatChunk(BaseModel):
    """A chunk of streaming chat response."""
    
    id: str = Field(..., description="Chunk identifier")
    conversation_id: str = Field(..., description="Conversation identifier")
    content: str = Field(..., description="Chunk content")
    is_final: bool = Field(default=False, description="Whether this is the final chunk")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "chunk_001",
                "conversation_id": "conv_67890",
                "content": "To transition into AI engineering",
                "is_final": False
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    
    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    version: str = Field(..., description="Application version")
    
    # Service dependencies
    azure_openai_status: Literal["connected", "disconnected", "error"] = Field(
        ..., description="Azure OpenAI connection status"
    )
    database_status: Literal["connected", "disconnected", "error"] = Field(
        ..., description="Database connection status"
    )
    
    # Performance metrics
    response_time_ms: Optional[int] = Field(None, description="Average response time")
    active_conversations: Optional[int] = Field(None, description="Currently active conversations")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-10-04T10:30:00Z",
                "version": "0.1.0",
                "azure_openai_status": "connected",
                "database_status": "connected",
                "response_time_ms": 850,
                "active_conversations": 12
            }
        }


class ErrorResponse(BaseModel):
    """Standardized error response model."""
    
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for tracing")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "error_code": "INVALID_MESSAGE",
                "message": "Message content cannot be empty",
                "timestamp": "2025-10-04T10:30:00Z",
                "request_id": "req_abc123"
            }
        }