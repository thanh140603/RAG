"""
VectorRetriever - Infrastructure Layer
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any

from src.domain.entities.RetrievedChunk import RetrievedChunk
from src.domain.repositories.EmbeddingRepository import EmbeddingRepository


class VectorRetriever:
    """
    Vector similarity retrieval using the embedding repository
    """

    def __init__(self, embedding_repository: EmbeddingRepository):
        self._embedding_repository = embedding_repository

    async def retrieve(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
    ) -> List[RetrievedChunk]:
        matches = await self._embedding_repository.search_similar(
            query_vector=query_vector,
            top_k=top_k,
            filter_metadata=filter_metadata,
            user_id=user_id,
            group_id=group_id,
        )
        retrieved: List[RetrievedChunk] = []
        for idx, (embedding, score) in enumerate(matches):
            retrieved.append(
                RetrievedChunk(
                    document_id=embedding.document_id,
                    chunk_id=embedding.chunk_id,
                    content=embedding.text,
                    score=score,
                    metadata=embedding.metadata or {},
                    rank=idx + 1,
                )
            )
        return retrieved

