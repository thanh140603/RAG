"""
BM25Retriever - Infrastructure Layer
Implements BM25 (Best Matching 25) keyword-based retrieval
"""
from __future__ import annotations

from typing import List, Optional

from src.domain.entities.RetrievedChunk import RetrievedChunk
from src.domain.repositories.ChunkRepository import ChunkRepository


class BM25Retriever:
    """
    BM25 keyword-based retriever
    Single Responsibility: Retrieve chunks using BM25 ranking algorithm
    """

    def __init__(self, chunk_repository: ChunkRepository):
        """
        Initialize BM25 retriever
        
        Args:
            chunk_repository: Repository with BM25 search implementation
        """
        self._chunk_repository = chunk_repository

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
    ) -> List[RetrievedChunk]:
        """
        Retrieve chunks using BM25 ranking
        
        The actual BM25 calculation is done in ChunkRepositoryImpl.search_bm25()
        """
        # Search chunks using repository's BM25 implementation
        bm25_results = await self._chunk_repository.search_bm25(
            query=query,
            top_k=top_k,
            user_id=user_id,
            group_id=group_id,
        )

        # Convert to RetrievedChunk entities
        retrieved: List[RetrievedChunk] = []
        for chunk, bm25_score in bm25_results:
            retrieved.append(
                RetrievedChunk(
                    document_id=str(chunk.document_id),
                    chunk_id=str(chunk.id),
                    content=chunk.text,
                    score=bm25_score,
                    metadata=chunk.metadata or {},
                    rank=len(retrieved) + 1,
                )
            )

        return retrieved

