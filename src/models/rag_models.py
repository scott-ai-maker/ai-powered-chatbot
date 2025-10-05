"""
RAG (Retrieval-Augmented Generation) models for the AI Career Mentor Chatbot.

This module defines the data models used for implementing RAG functionality
including knowledge base documents, search queries, and retrieval results.
Demonstrates advanced AI engineering patterns for enterprise RAG systems.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class DocumentType(str, Enum):
    """Types of documents in the knowledge base."""
    CAREER_GUIDE = "career_guide"
    TECHNICAL_SKILL = "technical_skill"
    INTERVIEW_PREP = "interview_prep"
    INDUSTRY_INSIGHT = "industry_insight"
    LEARNING_PATH = "learning_path"
    SALARY_DATA = "salary_data"
    COMPANY_INFO = "company_info"


class KnowledgeDocument(BaseModel):
    """
    Represents a document in the knowledge base for RAG retrieval.
    
    This model defines the structure of documents that will be indexed
    in Azure Cognitive Search and used for retrieval during conversations.
    """
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique document identifier")
    title: str = Field(..., min_length=1, max_length=200, description="Document title")
    content: str = Field(..., min_length=1, max_length=10000, description="Main document content")
    summary: str = Field(..., min_length=1, max_length=500, description="Brief document summary")
    document_type: DocumentType = Field(..., description="Type/category of the document")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    source_url: Optional[str] = Field(default=None, description="Source URL if applicable")
    author: Optional[str] = Field(default=None, description="Document author")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @field_validator('tags', mode='before')
    @classmethod
    def validate_tags(cls, v):
        """Validate and clean tags."""
        if isinstance(v, list):
            # Process each tag in the list
            cleaned_tags = []
            for tag in v:
                if not isinstance(tag, str):
                    raise ValueError('Tags must be strings')
                if len(tag.strip()) == 0:
                    raise ValueError('Tags cannot be empty')
                if len(tag) > 50:
                    raise ValueError('Tags must be 50 characters or less')
                cleaned_tags.append(tag.strip().lower())
            return list(set(cleaned_tags))  # Remove duplicates
        elif isinstance(v, str):
            # Single tag as string
            if len(v.strip()) == 0:
                raise ValueError('Tags cannot be empty')
            if len(v) > 50:
                raise ValueError('Tags must be 50 characters or less')
            return [v.strip().lower()]
        else:
            raise ValueError('Tags must be a list of strings or a single string')
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
        json_schema_extra = {
            "example": {
                "title": "Transitioning to AI Engineering: A Complete Guide",
                "content": "AI engineering is one of the fastest-growing fields...",
                "summary": "Comprehensive guide for professionals transitioning to AI engineering roles",
                "document_type": "career_guide",
                "tags": ["ai-engineering", "career-transition", "technical-skills"],
                "metadata": {"difficulty_level": "intermediate", "read_time_minutes": 15},
                "author": "AI Career Expert"
            }
        }


class SearchQuery(BaseModel):
    """
    Represents a search query for RAG retrieval.
    
    Contains the user's query along with context and filtering options
    for semantic search in the knowledge base.
    """
    query: str = Field(..., min_length=1, max_length=1000, description="Search query text")
    conversation_context: Optional[str] = Field(
        default=None, 
        max_length=2000, 
        description="Recent conversation context for better retrieval"
    )
    document_types: Optional[List[DocumentType]] = Field(
        default=None, 
        description="Filter by specific document types"
    )
    tags: Optional[List[str]] = Field(
        default=None, 
        description="Filter by specific tags"
    )
    max_results: int = Field(
        default=5, 
        ge=1, 
        le=20, 
        description="Maximum number of results to retrieve"
    )
    similarity_threshold: float = Field(
        default=0.7, 
        ge=0.0, 
        le=1.0, 
        description="Minimum similarity score for results"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "How do I prepare for machine learning interviews?",
                "conversation_context": "User is transitioning from software engineering",
                "document_types": ["interview_prep", "technical_skill"],
                "max_results": 3,
                "similarity_threshold": 0.8
            }
        }


class SearchResult(BaseModel):
    """
    Represents a single search result from RAG retrieval.
    
    Contains the retrieved document information along with relevance scoring
    and highlighted snippets for context.
    """
    document_id: str = Field(..., description="Retrieved document ID")
    title: str = Field(..., description="Document title")
    content_snippet: str = Field(..., description="Relevant content snippet")
    summary: str = Field(..., description="Document summary")
    document_type: DocumentType = Field(..., description="Document type")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    highlighted_snippets: List[str] = Field(
        default_factory=list, 
        description="Highlighted text snippets showing relevance"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_12345",
                "title": "Machine Learning Interview Questions",
                "content_snippet": "Common ML interview questions include algorithm complexity...",
                "summary": "Comprehensive guide to ML interview preparation",
                "document_type": "interview_prep",
                "similarity_score": 0.92,
                "tags": ["machine-learning", "interviews", "preparation"],
                "highlighted_snippets": ["algorithm complexity", "model evaluation"]
            }
        }


class RAGResponse(BaseModel):
    """
    Enhanced chat response that includes RAG retrieval information.
    
    Extends the basic chat response with retrieved context, sources,
    and confidence metrics for transparency and traceability.
    """
    message: str = Field(..., description="Generated response message")
    conversation_id: Optional[str] = Field(default=None, description="Conversation identifier")
    ai_model: str = Field(..., description="AI model used for generation")
    retrieved_sources: List[SearchResult] = Field(
        default_factory=list, 
        description="Sources used for RAG enhancement"
    )
    retrieval_query: Optional[str] = Field(
        default=None, 
        description="Query used for knowledge retrieval"
    )
    confidence_score: Optional[float] = Field(
        default=None, 
        ge=0.0, 
        le=1.0, 
        description="Response confidence score"
    )
    knowledge_enhanced: bool = Field(
        default=False, 
        description="Whether response was enhanced with retrieved knowledge"
    )
    processing_time_ms: int = Field(..., ge=0, description="Total processing time")
    retrieval_time_ms: Optional[int] = Field(
        default=None, 
        ge=0, 
        description="Time spent on knowledge retrieval"
    )
    generation_time_ms: Optional[int] = Field(
        default=None, 
        ge=0, 
        description="Time spent on response generation"
    )
    token_usage: Optional[Dict[str, int]] = Field(
        default=None, 
        description="Token usage statistics"
    )
    id: str = Field(default_factory=lambda: str(uuid4()), description="Response ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
        json_schema_extra = {
            "example": {
                "message": "Based on current industry trends, here are key skills for AI engineers...",
                "ai_model": "gpt-4",
                "retrieved_sources": [
                    {
                        "title": "AI Engineering Career Guide",
                        "similarity_score": 0.89,
                        "document_type": "career_guide"
                    }
                ],
                "knowledge_enhanced": True,
                "confidence_score": 0.92,
                "processing_time_ms": 1500,
                "retrieval_time_ms": 300,
                "generation_time_ms": 1200
            }
        }


class KnowledgeBaseStats(BaseModel):
    """
    Statistics about the knowledge base for monitoring and analytics.
    
    Provides insights into the knowledge base size, content distribution,
    and usage patterns for system optimization.
    """
    total_documents: int = Field(..., ge=0, description="Total number of documents")
    documents_by_type: Dict[DocumentType, int] = Field(
        ..., 
        description="Document count by type"
    )
    total_tags: int = Field(..., ge=0, description="Total number of unique tags")
    average_document_length: float = Field(..., ge=0, description="Average document length in characters")
    last_updated: datetime = Field(..., description="Last knowledge base update")
    search_performance: Dict[str, float] = Field(
        default_factory=dict, 
        description="Search performance metrics"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class IndexingStatus(BaseModel):
    """
    Status information for knowledge base indexing operations.
    
    Tracks the progress and results of document indexing operations
    in Azure Cognitive Search for operational monitoring.
    """
    operation_id: str = Field(..., description="Indexing operation identifier")
    status: str = Field(..., description="Operation status (pending, running, completed, failed)")
    documents_processed: int = Field(..., ge=0, description="Number of documents processed")
    documents_successful: int = Field(..., ge=0, description="Number of successfully indexed documents")
    documents_failed: int = Field(..., ge=0, description="Number of failed documents")
    start_time: datetime = Field(..., description="Operation start time")
    end_time: Optional[datetime] = Field(default=None, description="Operation end time")
    error_messages: List[str] = Field(
        default_factory=list, 
        description="Error messages if any"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


# Validation functions for enhanced data integrity would be added directly to model classes