"""
IndexDocumentUseCase - Application Layer
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import List
from uuid import uuid4

from src.domain.entities.Document import Document, DocumentStatus
from src.domain.entities.Embedding import Embedding
from src.domain.repositories.DocumentRepository import DocumentRepository
from src.infrastructure.rag.indexer.chunker import Chunker
from src.infrastructure.rag.indexer.embedder import Embedder
from src.infrastructure.rag.indexer.indexer_service import IndexerService
from src.infrastructure.rag.parser.document_parser import DocumentParser
from src.config.settings import get_settings
from src.infrastructure.storage.minio_storage import MinioStorageService

settings = get_settings()


class IndexDocumentUseCase:
    """
    Handles the full indexing workflow: load file -> chunk -> embed -> persist
    """

    def __init__(
        self,
        document_repository: DocumentRepository,
        chunker: Chunker,
        embedder: Embedder,
        indexer_service: IndexerService,
        storage_service: MinioStorageService | None = None,
        document_parser: DocumentParser | None = None,
    ):
        self._document_repository = document_repository
        self._chunker = chunker
        self._embedder = embedder
        self._indexer_service = indexer_service
        self._upload_dir = Path(settings.upload_directory)
        self._storage_service = storage_service
        self._document_parser = document_parser

    async def execute(self, document_id: str) -> Document:
        document = await self._document_repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        if document.is_indexed():
            return document

        document = await self._document_repository.update_status(
            document_id,
            DocumentStatus.PROCESSING,
        )

        try:
            content = await self._load_document_content(document)
            chunks = await self._chunker.chunk(content, document.id)
            vectors = await self._embedder.embed_batch([chunk.text for chunk in chunks])
            embeddings = self._build_embeddings(document, chunks, vectors)

            await self._indexer_service.index(chunks, embeddings)

            return await self._document_repository.update_status(
                document_id,
                DocumentStatus.INDEXED,
                chunk_count=len(chunks),
                indexed_at=datetime.utcnow(),
            )
        except Exception as exc:  # noqa: BLE001
            await self._document_repository.update_status(
                document_id,
                DocumentStatus.ERROR,
                error_message=str(exc),
            )
            raise

    async def _load_document_content(self, document: Document) -> str:
        storage_key = (document.metadata or {}).get("storage_key") if document.metadata else None
        file_bytes: bytes
        
        # Try MinIO first if storage_key is available
        if storage_key and self._storage_service:
            try:
                file_bytes = await self._storage_service.download_object(storage_key)
                if file_bytes:
                    # Successfully downloaded from MinIO
                    pass
                else:
                    raise FileNotFoundError(f"Downloaded file from MinIO is empty for storage_key: {storage_key}")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to download from MinIO (storage_key={storage_key}): {e}. Falling back to local path.")
                # Fall through to local path fallback
                storage_key = None
        
        # Fallback to local path if MinIO download failed or storage_key not available
        if not storage_key or not self._storage_service:
            path = (
                self._upload_dir
                / document.user_id
                / f"{document.id}_{document.filename}"
            )
            if not path.exists():
                raise FileNotFoundError(
                    f"Document source not found. "
                    f"Tried MinIO storage_key: {storage_key}, "
                    f"local path: {path}"
                )

            def _read_bytes() -> bytes:
                return path.read_bytes()

            file_bytes = await asyncio.to_thread(_read_bytes)

        if not file_bytes:
            return ""

        if self._document_parser:
            try:
                return await self._document_parser.parse(document.filename, file_bytes)
            except Exception:
                # Fallback to naive decode if parser fails
                pass

        return file_bytes.decode("utf-8", errors="ignore")

    def _build_embeddings(
        self,
        document: Document,
        chunks,
        vectors: List[List[float]],
    ) -> List[Embedding]:
        embeddings: List[Embedding] = []
        for chunk, vector in zip(chunks, vectors):
            embeddings.append(
                Embedding(
                    id=str(uuid4()),
                    document_id=document.id,
                    chunk_id=chunk.id,
                    text=chunk.text,
                    vector=vector,
                    metadata=chunk.metadata or {},
                )
            )
        return embeddings

