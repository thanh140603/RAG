"""
IndexerService - Infrastructure Layer
"""
from __future__ import annotations

from typing import List

from src.domain.entities.Chunk import Chunk
from src.domain.entities.Embedding import Embedding
from src.domain.repositories.ChunkRepository import ChunkRepository
from src.domain.repositories.EmbeddingRepository import EmbeddingRepository


class IndexerService:
    """
    Handles persistence of chunks and embeddings
    """

    def __init__(
        self,
        chunk_repository: ChunkRepository,
        embedding_repository: EmbeddingRepository,
    ):
        self._chunk_repository = chunk_repository
        self._embedding_repository = embedding_repository

    async def index(
        self,
        chunks: List[Chunk],
        embeddings: List[Embedding],
    ) -> None:
        if chunks:
            await self._chunk_repository.create_many(chunks)
        if embeddings:
            await self._embedding_repository.create_batch(embeddings)

