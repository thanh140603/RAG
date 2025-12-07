"""
Document ingestion pipeline service.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.usecases.IndexDocumentUseCase import IndexDocumentUseCase
from src.config.settings import get_settings
from src.infrastructure.database.postgres.connection import AsyncSessionLocal
from src.infrastructure.llm.openai_client import OpenAIClient
from src.infrastructure.rag.indexer.chunker import Chunker
from src.infrastructure.rag.indexer.embedder import Embedder
from src.infrastructure.rag.indexer.indexer_service import IndexerService
from src.infrastructure.rag.parser.document_parser import DocumentParser
from src.infrastructure.repositories.DocumentRepositoryImpl import DocumentRepositoryImpl
from src.infrastructure.repositories.ChunkRepositoryImpl import ChunkRepositoryImpl
from src.infrastructure.repositories.EmbeddingRepositoryImpl import EmbeddingRepositoryImpl
from src.infrastructure.storage.minio_storage import MinioStorageService


class DocumentIngestionService:
    """Runs the ingestion/indexing pipeline in the background."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] = AsyncSessionLocal,
        storage_service: MinioStorageService | None = None,
        document_parser: DocumentParser | None = None,
    ):
        self._session_factory = session_factory
        self._storage_service = storage_service
        self._document_parser = document_parser
        self._settings = get_settings()
        self._openai_client = OpenAIClient()

    async def ingest_document(self, document_id: str) -> None:
        """Run indexing for a document using a fresh DB session."""
        async with self._session_factory() as session:
            try:
                repo = DocumentRepositoryImpl(session)
                chunk_repo = ChunkRepositoryImpl(session)
                embedding_repo = EmbeddingRepositoryImpl(session)

                embedder = Embedder(openai_client=self._openai_client)
                # Use semantic chunking by default
                use_semantic = getattr(self._settings, "use_semantic_chunking", True)
                chunker = Chunker(use_semantic=use_semantic, embedder=embedder if use_semantic else None)
                indexer_service = IndexerService(
                    chunk_repository=chunk_repo,
                    embedding_repository=embedding_repo,
                )

                index_use_case = IndexDocumentUseCase(
                    document_repository=repo,
                    chunker=chunker,
                    embedder=embedder,
                    indexer_service=indexer_service,
                    storage_service=self._storage_service,
                    document_parser=self._document_parser,
                )
                await index_use_case.execute(document_id)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

