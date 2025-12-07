"""
RetrieverService - Infrastructure Layer
"""
from __future__ import annotations

from typing import List

from src.domain.entities.RetrievedChunk import RetrievedChunk
from src.infrastructure.rag.retriever.vector_retriever import VectorRetriever
from src.infrastructure.rag.retriever.hybrid_retriever import HybridRetriever
from src.config.settings import get_settings

settings = get_settings()


class RetrieverService:
    """
    Coordinates retrieval strategy (vector vs hybrid)
    """

    def __init__(
        self,
        vector_retriever: VectorRetriever,
        hybrid_retriever: HybridRetriever,
    ):
        self._vector_retriever = vector_retriever
        self._hybrid_retriever = hybrid_retriever

    async def retrieve(
        self,
        query: str,
        query_vector: List[float],
        top_k: int = 5,
        user_id: str | None = None,
        group_id: str | None = None,
    ) -> List[RetrievedChunk]:
        if settings.retrieval_method == "hybrid":
            return await self._hybrid_retriever.retrieve(
                query=query,
                query_vector=query_vector,
                top_k=top_k,
                user_id=user_id,
                group_id=group_id,
            )
        return await self._vector_retriever.retrieve(
            query_vector=query_vector,
            top_k=top_k,
            user_id=user_id,
            group_id=group_id,
        )

