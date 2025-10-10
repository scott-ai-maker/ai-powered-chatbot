"""
Azure Cognitive Search service for RAG implementation.

This service handles all interactions with Azure Cognitive Search including
document indexing, semantic search, and result processing for the RAG system.
Demonstrates enterprise-grade search integration for AI applications.
"""

import asyncio
import logging
from typing import List
from datetime import datetime, timezone
import json
import hashlib

from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticSearch,
    SemanticField,
    SemanticPrioritizedFields,
)
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError
from openai import AsyncAzureOpenAI

from src.config.settings import Settings
from src.models.rag_models import (
    KnowledgeDocument,
    SearchQuery,
    SearchResult,
    KnowledgeBaseStats,
    IndexingStatus,
    DocumentType,
)

logger = logging.getLogger(__name__)


class AzureCognitiveSearchService:
    """
    Service for managing Azure Cognitive Search operations for RAG.

    Handles document indexing, semantic search, vector search, and result
    processing for the knowledge-enhanced chatbot responses.
    """

    def __init__(self, settings: Settings):
        """Initialize the Azure Cognitive Search service."""
        self.settings = settings
        self.index_name = settings.azure_search_index_name

        # Initialize clients
        self.credential = AzureKeyCredential(settings.azure_search_key)
        self.search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name=self.index_name,
            credential=self.credential,
        )
        self.index_client = SearchIndexClient(
            endpoint=settings.azure_search_endpoint, credential=self.credential
        )

        # Initialize OpenAI client for embeddings
        self.openai_client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
        )

        # Search configuration
        self.vector_search_dimensions = 1536  # text-embedding-ada-002 dimensions
        self.max_retries = 3
        self.retry_delay = 1.0

    async def initialize_index(self) -> bool:
        """
        Initialize the search index with proper schema for RAG documents.

        Creates a new index with vector search capabilities, semantic search,
        and proper field mappings for knowledge documents.
        """
        try:
            # Define the search index schema
            fields = [
                SimpleField(
                    name="id",
                    type=SearchFieldDataType.String,
                    key=True,
                    filterable=True,
                ),
                SearchableField(
                    name="title",
                    type=SearchFieldDataType.String,
                    searchable=True,
                    retrievable=True,
                    analyzer_name="en.microsoft",
                ),
                SearchableField(
                    name="content",
                    type=SearchFieldDataType.String,
                    searchable=True,
                    retrievable=True,
                    analyzer_name="en.microsoft",
                ),
                SearchableField(
                    name="summary",
                    type=SearchFieldDataType.String,
                    searchable=True,
                    retrievable=True,
                    analyzer_name="en.microsoft",
                ),
                SimpleField(
                    name="document_type",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    facetable=True,
                ),
                SearchableField(
                    name="tags",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                    searchable=True,
                    filterable=True,
                    facetable=True,
                ),
                SimpleField(
                    name="metadata", type=SearchFieldDataType.String, retrievable=True
                ),
                SimpleField(
                    name="source_url", type=SearchFieldDataType.String, retrievable=True
                ),
                SimpleField(
                    name="author",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    facetable=True,
                ),
                SimpleField(
                    name="created_at",
                    type=SearchFieldDataType.DateTimeOffset,
                    filterable=True,
                    sortable=True,
                ),
                SimpleField(
                    name="updated_at",
                    type=SearchFieldDataType.DateTimeOffset,
                    filterable=True,
                    sortable=True,
                ),
                SearchField(
                    name="content_vector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=self.vector_search_dimensions,
                    vector_search_profile_name="my-vector-config",
                ),
            ]

            # Configure vector search
            vector_search = VectorSearch(
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="my-hnsw-config",
                        parameters={
                            "m": 4,
                            "efConstruction": 400,
                            "efSearch": 500,
                            "metric": "cosine",
                        },
                    )
                ],
                profiles=[
                    VectorSearchProfile(
                        name="my-vector-config",
                        algorithm_configuration_name="my-hnsw-config",
                    )
                ],
            )

            # Configure semantic search
            semantic_config = SemanticConfiguration(
                name="my-semantic-config",
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name="title"),
                    keywords_fields=[SemanticField(field_name="tags")],
                    content_fields=[
                        SemanticField(field_name="content"),
                        SemanticField(field_name="summary"),
                    ],
                ),
            )

            semantic_search = SemanticSearch(configurations=[semantic_config])

            # Create the search index
            index = SearchIndex(
                name=self.index_name,
                fields=fields,
                vector_search=vector_search,
                semantic_search=semantic_search,
            )

            # Create or update the index
            result = await self.index_client.create_or_update_index(index)
            logger.info(f"Successfully created/updated search index: {result.name}")
            return True

        except AzureError as e:
            logger.error(f"Failed to initialize search index: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error initializing search index: {e}")
            return False

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text using Azure OpenAI.

        Args:
            text: Text to generate embedding for

        Returns:
            List of float values representing the text embedding
        """
        try:
            response = await self.openai_client.embeddings.create(
                input=text, model="text-embedding-ada-002"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def index_document(self, document: KnowledgeDocument) -> bool:
        """
        Index a single document in Azure Cognitive Search.

        Args:
            document: Knowledge document to index

        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate embedding for the document content
            content_text = f"{document.title} {document.summary} {document.content}"
            content_vector = await self.generate_embedding(content_text)

            # Prepare document for indexing
            search_document = {
                "id": document.id,
                "title": document.title,
                "content": document.content,
                "summary": document.summary,
                "document_type": document.document_type.value,
                "tags": document.tags,
                "metadata": json.dumps(document.metadata),
                "source_url": document.source_url,
                "author": document.author,
                "created_at": document.created_at.isoformat(),
                "updated_at": document.updated_at.isoformat(),
                "content_vector": content_vector,
            }

            # Upload document to search index
            result = await self.search_client.upload_documents([search_document])

            if result[0].succeeded:
                logger.info(f"Successfully indexed document: {document.id}")
                return True
            else:
                logger.error(
                    f"Failed to index document {document.id}: {result[0].error_message}"
                )
                return False

        except Exception as e:
            logger.error(f"Error indexing document {document.id}: {e}")
            return False

    async def index_documents_batch(
        self, documents: List[KnowledgeDocument]
    ) -> IndexingStatus:
        """
        Index multiple documents in batch for efficiency.

        Args:
            documents: List of knowledge documents to index

        Returns:
            IndexingStatus with operation results
        """
        operation_id = hashlib.md5(
            f"{datetime.now().isoformat()}_{len(documents)}".encode()
        ).hexdigest()

        status = IndexingStatus(
            operation_id=operation_id,
            status="running",
            documents_processed=0,
            documents_successful=0,
            documents_failed=0,
            start_time=datetime.now(timezone.utc),
            error_messages=[],
        )

        try:
            # Process documents in smaller batches to avoid timeouts
            batch_size = 10
            for i in range(0, len(documents), batch_size):
                batch = documents[i : i + batch_size]
                batch_documents = []

                for document in batch:
                    try:
                        # Generate embedding
                        content_text = (
                            f"{document.title} {document.summary} {document.content}"
                        )
                        content_vector = await self.generate_embedding(content_text)

                        # Prepare document
                        search_document = {
                            "id": document.id,
                            "title": document.title,
                            "content": document.content,
                            "summary": document.summary,
                            "document_type": document.document_type.value,
                            "tags": document.tags,
                            "metadata": json.dumps(document.metadata),
                            "source_url": document.source_url,
                            "author": document.author,
                            "created_at": document.created_at.isoformat(),
                            "updated_at": document.updated_at.isoformat(),
                            "content_vector": content_vector,
                        }
                        batch_documents.append(search_document)

                    except Exception as e:
                        status.documents_failed += 1
                        status.error_messages.append(
                            f"Document {document.id}: {str(e)}"
                        )
                        continue

                # Upload batch
                if batch_documents:
                    try:
                        results = await self.search_client.upload_documents(
                            batch_documents
                        )
                        for result in results:
                            if result.succeeded:
                                status.documents_successful += 1
                            else:
                                status.documents_failed += 1
                                status.error_messages.append(
                                    f"Document {result.key}: {result.error_message}"
                                )
                    except Exception as e:
                        status.documents_failed += len(batch_documents)
                        status.error_messages.append(f"Batch upload error: {str(e)}")

                status.documents_processed += len(batch)

                # Small delay between batches
                await asyncio.sleep(0.1)

            status.status = "completed"
            status.end_time = datetime.now(timezone.utc)

        except Exception as e:
            status.status = "failed"
            status.end_time = datetime.now(timezone.utc)
            status.error_messages.append(f"Operation failed: {str(e)}")

        logger.info(
            f"Indexing operation {operation_id} completed: "
            f"{status.documents_successful} successful, {status.documents_failed} failed"
        )

        return status

    async def semantic_search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Perform semantic search using Azure Cognitive Search.

        Args:
            query: Search query with parameters

        Returns:
            List of search results with relevance scores
        """
        try:
            # Generate query embedding for vector search
            query_vector = await self.generate_embedding(query.query)

            # Build search parameters
            search_params = {
                "search_text": query.query,
                "top": query.max_results,
                "query_type": "semantic",
                "semantic_configuration_name": "my-semantic-config",
                "query_caption": "extractive",
                "query_answer": "extractive",
            }

            # Add vector search
            vector_query = VectorizedQuery(
                vector=query_vector,
                k_nearest_neighbors=query.max_results,
                fields="content_vector",
            )
            search_params["vector_queries"] = [vector_query]

            # Add filters if specified
            filter_conditions = []
            if query.document_types:
                type_filter = " or ".join(
                    [f"document_type eq '{dt.value}'" for dt in query.document_types]
                )
                filter_conditions.append(f"({type_filter})")

            if query.tags:
                tag_filters = []
                for tag in query.tags:
                    tag_filters.append(f"tags/any(t: t eq '{tag}')")
                if tag_filters:
                    filter_conditions.append(f"({' or '.join(tag_filters)})")

            if filter_conditions:
                search_params["filter"] = " and ".join(filter_conditions)

            # Perform search
            results = await self.search_client.search(**search_params)

            # Process results
            search_results = []
            async for result in results:
                # Calculate similarity score (hybrid of semantic and vector scores)
                semantic_score = getattr(result, "@search.reranker_score", 0.0) or 0.0
                vector_score = getattr(result, "@search.score", 0.0) or 0.0
                similarity_score = max(
                    semantic_score / 4.0, vector_score
                )  # Normalize semantic score

                # Skip results below threshold
                if similarity_score < query.similarity_threshold:
                    continue

                # Extract highlighted snippets
                captions = getattr(result, "@search.captions", [])
                highlighted_snippets = []
                if captions:
                    for caption in captions:
                        if hasattr(caption, "text"):
                            highlighted_snippets.append(caption.text)

                # Parse metadata
                metadata = {}
                if result.get("metadata"):
                    try:
                        metadata = json.loads(result["metadata"])
                    except (json.JSONDecodeError, TypeError):
                        pass

                search_result = SearchResult(
                    document_id=result["id"],
                    title=result["title"],
                    content_snippet=result["content"][:500] + "..."
                    if len(result["content"]) > 500
                    else result["content"],
                    summary=result["summary"],
                    document_type=DocumentType(result["document_type"]),
                    similarity_score=min(similarity_score, 1.0),  # Cap at 1.0
                    tags=result.get("tags", []),
                    metadata=metadata,
                    highlighted_snippets=highlighted_snippets,
                )

                search_results.append(search_result)

            # Sort by similarity score
            search_results.sort(key=lambda x: x.similarity_score, reverse=True)

            logger.info(
                f"Semantic search returned {len(search_results)} results for query: {query.query[:50]}..."
            )
            return search_results

        except Exception as e:
            logger.error(f"Error performing semantic search: {e}")
            return []

    async def get_knowledge_base_stats(self) -> KnowledgeBaseStats:
        """
        Get statistics about the knowledge base.

        Returns:
            Knowledge base statistics and metrics
        """
        try:
            # Get total document count
            count_results = await self.search_client.search(
                search_text="*", include_total_count=True, top=0
            )
            total_documents = count_results.get_count()

            # Get documents by type
            facet_results = await self.search_client.search(
                search_text="*", facets=["document_type"], top=0
            )

            documents_by_type = {}
            facets = facet_results.get_facets()
            if facets and "document_type" in facets:
                for facet in facets["document_type"]:
                    doc_type = DocumentType(facet["value"])
                    documents_by_type[doc_type] = facet["count"]

            # Calculate average document length (approximate)
            sample_results = await self.search_client.search(
                search_text="*", top=100, select=["content"]
            )

            total_length = 0
            sample_count = 0
            async for result in sample_results:
                if result.get("content"):
                    total_length += len(result["content"])
                    sample_count += 1

            average_length = total_length / sample_count if sample_count > 0 else 0

            return KnowledgeBaseStats(
                total_documents=total_documents or 0,
                documents_by_type=documents_by_type,
                total_tags=0,  # Would need additional query to calculate
                average_document_length=average_length,
                last_updated=datetime.now(timezone.utc),
                search_performance={},  # Would be populated by monitoring
            )

        except Exception as e:
            logger.error(f"Error getting knowledge base stats: {e}")
            return KnowledgeBaseStats(
                total_documents=0,
                documents_by_type={},
                total_tags=0,
                average_document_length=0,
                last_updated=datetime.now(timezone.utc),
                search_performance={},
            )

    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the search index.

        Args:
            document_id: ID of document to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.search_client.delete_documents([{"id": document_id}])
            if result[0].succeeded:
                logger.info(f"Successfully deleted document: {document_id}")
                return True
            else:
                logger.error(
                    f"Failed to delete document {document_id}: {result[0].error_message}"
                )
                return False
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False

    async def close(self):
        """Close the search client connections."""
        try:
            await self.search_client.close()
            await self.index_client.close()
            await self.openai_client.close()
        except Exception as e:
            logger.error(f"Error closing search clients: {e}")
