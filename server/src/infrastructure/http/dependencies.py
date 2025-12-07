"""
HTTP Dependency Providers
Single Responsibility: Wire application components for FastAPI DI
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.usecases.ChatCompletionUseCase import ChatCompletionUseCase
from src.application.usecases.IndexDocumentUseCase import IndexDocumentUseCase
from src.application.usecases.QueryRAGUseCase import QueryRAGUseCase
from src.application.usecases.UploadFileUseCase import UploadFileUseCase
from src.application.services.DocumentIngestionService import DocumentIngestionService
from src.domain.repositories.ChatRepository import ChatRepository
from src.domain.repositories.DocumentRepository import DocumentRepository
from src.domain.repositories.DocumentGroupRepository import DocumentGroupRepository
from src.domain.repositories.RAGRepository import RAGRepository
from src.domain.repositories.ApiTokenUsageRepository import ApiTokenUsageRepository
from src.config.settings import get_settings
from src.infrastructure.database.postgres.connection import get_db
from src.infrastructure.llm.openai_client import OpenAIClient
from src.infrastructure.rag.external.web_search_service import WebSearchService
from src.infrastructure.rag.generator.llm_generator import LLMGenerator
from src.infrastructure.rag.indexer.chunker import Chunker
from src.infrastructure.rag.indexer.embedder import Embedder
from src.infrastructure.rag.indexer.indexer_service import IndexerService
from src.infrastructure.rag.parser.document_parser import DocumentParser
from src.infrastructure.rag.query_transformation.multi_query import MultiQueryGenerator
from src.infrastructure.rag.query_transformation.step_back_prompt import StepBackPromptGenerator
from src.infrastructure.rag.reranker.rrf_fusion import RRFFusion
from src.infrastructure.rag.retriever.bm25_retriever import BM25Retriever
from src.infrastructure.rag.retriever.hybrid_retriever import HybridRetriever
from src.infrastructure.rag.retriever.retriever_service import RetrieverService
from src.infrastructure.rag.retriever.vector_retriever import VectorRetriever
from src.infrastructure.repositories.ChatRepositoryImpl import ChatRepositoryImpl
from src.infrastructure.repositories.ChunkRepositoryImpl import ChunkRepositoryImpl
from src.infrastructure.repositories.DocumentRepositoryImpl import DocumentRepositoryImpl
from src.infrastructure.repositories.DocumentGroupRepositoryImpl import DocumentGroupRepositoryImpl
from src.infrastructure.repositories.EmbeddingRepositoryImpl import EmbeddingRepositoryImpl
from src.infrastructure.repositories.RAGRepositoryImpl import RAGRepositoryImpl
from src.infrastructure.repositories.ApiTokenUsageRepositoryImpl import ApiTokenUsageRepositoryImpl
from src.infrastructure.services.token_tracker import TokenTracker
from src.infrastructure.storage.minio_storage import MinioStorageService


@lru_cache(maxsize=1)
def _get_openai_client_cached() -> OpenAIClient:
    """Return singleton OpenAI client instance."""
    return OpenAIClient()


def get_openai_client() -> OpenAIClient:
    """Expose cached OpenAI client."""
    return _get_openai_client_cached()


def get_storage_service() -> MinioStorageService:
    """Provide storage service (currently MinIO)."""
    settings = get_settings()
    if settings.storage_provider != "minio":
        raise ValueError(f"Unsupported storage provider: {settings.storage_provider}")
    try:
        return MinioStorageService(settings=settings)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to initialize MinIO storage: {e}")
        return MinioStorageService(settings=settings)


@lru_cache(maxsize=1)
def get_document_parser() -> DocumentParser:
    """Provide reusable document parser."""
    return DocumentParser()


async def get_rag_repository(
    db: AsyncSession = Depends(get_db),
) -> RAGRepository:
    """Build RAG repository with all retrieval dependencies."""
    openai_client = get_openai_client()

    embedder = Embedder(openai_client=openai_client)
    chunk_repository = ChunkRepositoryImpl(db_session=db)
    embedding_repository = EmbeddingRepositoryImpl(db_session=db)

    vector_retriever = VectorRetriever(embedding_repository=embedding_repository)
    bm25_retriever = BM25Retriever(chunk_repository=chunk_repository)
    hybrid_retriever = HybridRetriever(
        vector_retriever=vector_retriever,
        bm25_retriever=bm25_retriever,
    )
    retriever_service = RetrieverService(
        vector_retriever=vector_retriever,
        hybrid_retriever=hybrid_retriever,
    )

    return RAGRepositoryImpl(
        retriever=retriever_service,
        embedder=embedder,
        db_session=db,
    )


async def get_api_token_usage_repository(
    db: AsyncSession = Depends(get_db),
) -> ApiTokenUsageRepository:
    """Provide API token usage repository."""
    return ApiTokenUsageRepositoryImpl(db_session=db)


async def get_token_tracker(
    token_repository: ApiTokenUsageRepository = Depends(get_api_token_usage_repository),
) -> TokenTracker:
    """Provide TokenTracker for tracking API usage."""
    return TokenTracker(token_repository=token_repository)


async def get_web_search_service(
    token_tracker: TokenTracker = Depends(get_token_tracker),
) -> WebSearchService | None:
    """Provide web search service if enabled."""
    settings = get_settings()
    if settings.enable_web_search:
        return WebSearchService(token_tracker=token_tracker)
    return None


async def get_query_rag_use_case(
    rag_repository: RAGRepository = Depends(get_rag_repository),
    web_search_service: WebSearchService | None = Depends(get_web_search_service),
    token_tracker: TokenTracker = Depends(get_token_tracker),
) -> QueryRAGUseCase:
    """Construct QueryRAGUseCase with generators, reranker, and optional web search."""
    openai_client = get_openai_client()
    multi_query_generator = MultiQueryGenerator(llm_client=openai_client)
    step_back_generator = StepBackPromptGenerator(llm_client=openai_client)
    reranker = RRFFusion()
    llm_generator = LLMGenerator(llm_client=openai_client, token_tracker=token_tracker)

    return QueryRAGUseCase(
        rag_repository=rag_repository,
        multi_query_generator=multi_query_generator,
        step_back_generator=step_back_generator,
        reranker=reranker,
        llm_generator=llm_generator,
        web_search_service=web_search_service,
    )


async def get_chat_repository(
    db: AsyncSession = Depends(get_db),
) -> ChatRepository:
    """Provide chat repository."""
    return ChatRepositoryImpl(db_session=db)


async def get_chat_completion_use_case(
    query_rag_use_case: QueryRAGUseCase = Depends(get_query_rag_use_case),
    chat_repository: ChatRepository = Depends(get_chat_repository),
) -> ChatCompletionUseCase:
    """Provide ChatCompletionUseCase dependency with conversation history support."""
    return ChatCompletionUseCase(
        query_rag_use_case=query_rag_use_case,
        chat_repository=chat_repository,
    )


async def get_document_repository(
    db: AsyncSession = Depends(get_db),
) -> DocumentRepository:
    """Provide document repository."""
    return DocumentRepositoryImpl(db_session=db)


async def get_document_group_repository(
    db: AsyncSession = Depends(get_db),
) -> DocumentGroupRepository:
    """Provide document group repository."""
    return DocumentGroupRepositoryImpl(session=db)


async def get_index_document_use_case(
    db: AsyncSession = Depends(get_db),
    document_repository: DocumentRepository = Depends(get_document_repository),
    storage_service: MinioStorageService = Depends(get_storage_service),
    document_parser: DocumentParser = Depends(get_document_parser),
) -> IndexDocumentUseCase:
    """Build IndexDocumentUseCase with chunking + embedding dependencies."""
    from src.config.settings import get_settings
    settings = get_settings()
    
    openai_client = get_openai_client()
    embedder = Embedder(openai_client=openai_client    )
    use_semantic = settings.use_semantic_chunking
    chunker = Chunker(use_semantic=use_semantic, embedder=embedder if use_semantic else None)
    chunk_repo = ChunkRepositoryImpl(db_session=db)
    embedding_repo = EmbeddingRepositoryImpl(db_session=db)
    indexer_service = IndexerService(
        chunk_repository=chunk_repo,
        embedding_repository=embedding_repo,
    )
    return IndexDocumentUseCase(
        document_repository=document_repository,
        chunker=chunker,
        embedder=embedder,
        indexer_service=indexer_service,
        storage_service=storage_service,
        document_parser=document_parser,
    )


async def get_upload_file_use_case(
    document_repository: DocumentRepository = Depends(get_document_repository),
    index_document_use_case: IndexDocumentUseCase = Depends(get_index_document_use_case),
) -> UploadFileUseCase:
    """Provide UploadFileUseCase that can trigger indexing."""
    return UploadFileUseCase(
        document_repository=document_repository,
        index_document_use_case=index_document_use_case,
    )


def get_document_ingestion_service(
    storage_service: MinioStorageService = Depends(get_storage_service),
    document_parser: DocumentParser = Depends(get_document_parser),
) -> DocumentIngestionService:
    """Provide ingestion pipeline service."""
    return DocumentIngestionService(storage_service=storage_service, document_parser=document_parser)


