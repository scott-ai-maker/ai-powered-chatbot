"""
Integration tests for RAG (Retrieval-Augmented Generation) functionality.

This module tests the complete RAG pipeline including:
- Knowledge base seeding
- Document search and retrieval
- RAG-enhanced response generation
- API endpoint integration

These tests demonstrate the full capabilities of the knowledge-enhanced
chatbot system and validate production-ready functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.models.rag_models import (
    KnowledgeDocument,
    DocumentType,
    SearchQuery,
    RAGResponse,
    SearchResult,
)
from src.services.search_service import AzureCognitiveSearchService
from src.services.rag_service import RAGEnhancedAIService
from src.services.knowledge_seeder import KnowledgeBaseSeeder
from src.config.settings import Settings


class TestRAGModels:
    """Test RAG data models and validation."""

    def test_knowledge_document_creation(self):
        """Test creating and validating KnowledgeDocument."""
        doc = KnowledgeDocument(
            title="Test Career Guide",
            content="This is a comprehensive guide to AI careers...",
            summary="Career transition guide for AI engineering",
            document_type=DocumentType.CAREER_GUIDE,
            tags=["career", "ai", "engineering"],
            metadata={"difficulty": "beginner", "read_time": 10},
            author="Test Author",
        )

        assert doc.title == "Test Career Guide"
        assert doc.document_type == DocumentType.CAREER_GUIDE
        assert "career" in doc.tags
        assert doc.metadata["difficulty"] == "beginner"
        assert doc.id is not None  # Should be auto-generated
        assert doc.created_at is not None

    def test_search_query_validation(self):
        """Test SearchQuery validation and defaults."""
        query = SearchQuery(query="AI engineer interview tips")

        assert query.query == "AI engineer interview tips"
        assert query.max_results == 10  # Default value
        assert query.min_confidence_score == 0.7  # Default value
        assert query.document_types is None  # Default value

    def test_search_query_with_filters(self):
        """Test SearchQuery with custom filters."""
        query = SearchQuery(
            query="salary information",
            max_results=5,
            min_confidence_score=0.8,
            document_types=[DocumentType.SALARY_DATA, DocumentType.INDUSTRY_INSIGHT],
        )

        assert query.max_results == 5
        assert query.min_confidence_score == 0.8
        assert len(query.document_types) == 2


class TestKnowledgeBaseSeeder:
    """Test knowledge base seeding functionality."""

    @pytest.fixture
    def mock_search_service(self):
        """Mock search service for testing."""
        service = MagicMock(spec=AzureCognitiveSearchService)
        service.index_documents_batch = AsyncMock()
        return service

    @pytest.fixture
    def seeder(self, mock_search_service):
        """Create knowledge base seeder with mocked dependencies."""
        return KnowledgeBaseSeeder(mock_search_service)

    def test_sample_documents_generation(self, seeder):
        """Test generation of sample knowledge documents."""
        documents = seeder.get_sample_documents()

        assert len(documents) > 0
        assert all(isinstance(doc, KnowledgeDocument) for doc in documents)

        # Check we have different document types
        doc_types = {doc.document_type for doc in documents}
        expected_types = {
            DocumentType.CAREER_GUIDE,
            DocumentType.TECHNICAL_SKILL,
            DocumentType.INTERVIEW_PREP,
            DocumentType.SALARY_DATA,
            DocumentType.LEARNING_PATH,
            DocumentType.INDUSTRY_INSIGHT,
        }
        assert doc_types == expected_types

    def test_document_content_quality(self, seeder):
        """Test that generated documents have quality content."""
        documents = seeder.get_sample_documents()

        for doc in documents:
            # Check content length is substantial
            assert len(doc.content) > 1000, (
                f"Document '{doc.title}' has insufficient content"
            )

            # Check required fields are populated
            assert doc.title and len(doc.title) > 10
            assert doc.summary and len(doc.summary) > 50
            assert doc.tags and len(doc.tags) > 0
            assert doc.author

            # Check metadata contains useful information
            assert doc.metadata
            assert "difficulty_level" in doc.metadata
            assert "read_time_minutes" in doc.metadata

    @pytest.mark.asyncio
    async def test_successful_seeding(self, seeder, mock_search_service):
        """Test successful knowledge base seeding."""
        # Mock successful indexing
        from src.models.rag_models import IndexingStatus

        mock_status = IndexingStatus(
            status="completed",
            documents_processed=6,
            documents_successful=6,
            documents_failed=0,
            error_messages=[],
        )
        mock_search_service.index_documents_batch.return_value = mock_status

        result = await seeder.seed_knowledge_base()

        assert result is True
        mock_search_service.index_documents_batch.assert_called_once()

        # Check that documents were passed to the search service
        call_args = mock_search_service.index_documents_batch.call_args[0][0]
        assert len(call_args) == 6  # Should be 6 sample documents

    @pytest.mark.asyncio
    async def test_failed_seeding(self, seeder, mock_search_service):
        """Test handling of failed knowledge base seeding."""
        # Mock failed indexing
        from src.models.rag_models import IndexingStatus

        mock_status = IndexingStatus(
            status="failed",
            documents_processed=6,
            documents_successful=4,
            documents_failed=2,
            error_messages=["Document 1 failed", "Document 2 failed"],
        )
        mock_search_service.index_documents_batch.return_value = mock_status

        result = await seeder.seed_knowledge_base()

        assert result is False


class TestRAGService:
    """Test RAG-enhanced AI service."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        settings = MagicMock(spec=Settings)
        settings.azure_openai_endpoint = "https://test.openai.azure.com"
        settings.azure_openai_key = "test-key"
        settings.azure_openai_deployment_name = "gpt-4"
        settings.rag_max_search_results = 5
        settings.rag_min_confidence_score = 0.7
        return settings

    @pytest.fixture
    def mock_search_service(self):
        """Mock search service for testing."""
        service = MagicMock(spec=AzureCognitiveSearchService)
        service.semantic_search = AsyncMock()
        return service

    @pytest.fixture
    def rag_service(self, mock_settings, mock_search_service):
        """Create RAG service with mocked dependencies."""
        with patch("src.services.rag_service.AsyncAzureOpenAI"):
            service = RAGEnhancedAIService(mock_settings, mock_search_service)
            return service

    @pytest.mark.asyncio
    async def test_rag_response_generation(self, rag_service, mock_search_service):
        """Test RAG response generation with mocked search results."""
        # Mock search results
        from src.models.rag_models import SearchResults

        mock_results = SearchResults(
            results=[
                SearchResult(
                    title="AI Career Guide",
                    content="Complete guide to AI careers...",
                    summary="Comprehensive career guidance",
                    document_type=DocumentType.CAREER_GUIDE,
                    confidence_score=0.9,
                    tags=["career", "ai"],
                    metadata={"difficulty": "beginner"},
                )
            ],
            total_results=1,
            processing_time_ms=150,
        )
        mock_search_service.semantic_search.return_value = mock_results

        # Mock OpenAI response
        with patch.object(rag_service, "_client") as mock_client:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[
                0
            ].message.content = "Based on the career guide, here's my advice..."
            mock_response.model = "gpt-4"
            mock_response.usage.total_tokens = 500

            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            # Test RAG response generation
            response = await rag_service.generate_rag_response(
                message="How do I transition to AI engineering?",
                conversation_id="test-123",
                user_id="user-456",
            )

            assert isinstance(response, RAGResponse)
            assert response.response == "Based on the career guide, here's my advice..."
            assert len(response.sources) == 1
            assert response.sources[0].title == "AI Career Guide"
            assert response.confidence_score > 0
            assert response.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_rag_query_classification(self, rag_service):
        """Test that RAG service correctly identifies when to use retrieval."""
        # Career-related queries should use RAG
        career_queries = [
            "How much do AI engineers make?",
            "What skills do I need for machine learning?",
            "How to prepare for AI interviews?",
            "Best resources to learn deep learning?",
        ]

        for query in career_queries:
            should_use_rag = rag_service._should_use_rag(query)
            assert should_use_rag, f"Query '{query}' should use RAG"

        # Generic conversation should not use RAG
        generic_queries = [
            "Hello, how are you?",
            "What's the weather like?",
            "Tell me a joke",
            "What's 2 + 2?",
        ]

        for query in generic_queries:
            should_use_rag = rag_service._should_use_rag(query)
            assert not should_use_rag, f"Query '{query}' should not use RAG"

    def test_context_prompt_building(self, rag_service):
        """Test building context-aware prompts with retrieved information."""
        # Mock search results
        search_results = [
            SearchResult(
                title="AI Salary Guide 2024",
                content="AI engineers earn $120k-$300k based on experience...",
                summary="Salary information for AI engineers",
                document_type=DocumentType.SALARY_DATA,
                confidence_score=0.95,
                tags=["salary", "compensation"],
                metadata={"year": "2024"},
            )
        ]

        prompt = rag_service._build_context_prompt(
            "How much do AI engineers make?",
            search_results,
            [],  # No conversation history for this test
        )

        assert "AI Salary Guide 2024" in prompt
        assert "$120k-$300k" in prompt
        assert "How much do AI engineers make?" in prompt
        assert "Based on the following information" in prompt


class TestRAGIntegration:
    """Integration tests for the complete RAG system."""

    @pytest.mark.asyncio
    async def test_end_to_end_rag_workflow(self):
        """Test complete RAG workflow from seeding to response generation."""
        # This would be a more comprehensive integration test
        # that would require actual Azure services or more sophisticated mocking

        # For now, we'll test the workflow structure
        mock_settings = MagicMock(spec=Settings)

        with (
            patch("src.services.search_service.SearchClient"),
            patch("src.services.rag_service.AsyncAzureOpenAI"),
        ):
            # Initialize services
            search_service = AzureCognitiveSearchService(mock_settings)
            rag_service = RAGEnhancedAIService(mock_settings, search_service)
            seeder = KnowledgeBaseSeeder(search_service)

            # Verify services are properly initialized
            assert search_service is not None
            assert rag_service is not None
            assert seeder is not None

            # Verify service relationships
            assert rag_service.search_service is search_service
            assert seeder.search_service is search_service


class TestRAGAPIEndpoints:
    """Test RAG-enhanced API endpoints."""

    def test_rag_endpoint_structure(self):
        """Test that RAG endpoints are properly structured."""
        # This would test the actual FastAPI endpoints
        # For now, we verify the endpoint definitions exist
        from src.api.endpoints.chat import router

        # Check that RAG routes are defined
        routes = [route.path for route in router.routes]

        assert "/chat/rag" in routes
        assert "/chat/rag/stream" in routes
        assert "/search" in routes
        assert "/knowledge/stats" in routes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
