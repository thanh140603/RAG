"""
HybridRetriever - Infrastructure Layer
Combines BM25 (keyword) + Vector (semantic) retrieval
"""
from __future__ import annotations

from typing import List, Dict, Optional

from src.domain.entities.RetrievedChunk import RetrievedChunk
from src.infrastructure.rag.retriever.vector_retriever import VectorRetriever
from src.infrastructure.rag.retriever.bm25_retriever import BM25Retriever


class HybridRetriever:
    """
    Hybrid retrieval combining BM25 (keyword) + Vector (semantic) search
    Single Responsibility: Combine keyword and semantic retrieval results
    """

    def __init__(
        self,
        vector_retriever: VectorRetriever,
        bm25_retriever: BM25Retriever,
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5,
    ):
        """
        Initialize hybrid retriever
        
        Args:
            vector_retriever: Vector similarity retriever
            bm25_retriever: BM25 keyword retriever
            vector_weight: Weight for vector scores (default 0.5)
            bm25_weight: Weight for BM25 scores (default 0.5)
        """
        self._vector_retriever = vector_retriever
        self._bm25_retriever = bm25_retriever
        self._vector_weight = vector_weight
        self._bm25_weight = bm25_weight

    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """Normalize scores to [0, 1] range using min-max normalization"""
        if not scores:
            return []
        min_score = min(scores)
        max_score = max(scores)
        if max_score == min_score:
            return [1.0] * len(scores)
        return [(s - min_score) / (max_score - min_score) for s in scores]

    async def retrieve(
        self,
        query: str,
        query_vector: List[float],
        top_k: int = 5,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
    ) -> List[RetrievedChunk]:
        """
        Retrieve chunks using hybrid BM25 + Vector approach
        
        1. Get results from both retrievers
        2. Normalize scores to [0, 1] range
        3. Combine scores using weighted average
        4. Return top_k results
        """
        # Retrieve from both methods
        vector_results = await self._vector_retriever.retrieve(
            query_vector=query_vector,
            top_k=top_k * 2,  # Get more candidates for fusion
            user_id=user_id,
            group_id=group_id,
        )

        bm25_results = await self._bm25_retriever.retrieve(
            query=query,
            top_k=top_k * 2,  # Get more candidates for fusion
            user_id=user_id,
            group_id=group_id,
        )

        # Create lookup maps: (document_id, chunk_id) -> RetrievedChunk
        vector_map: Dict[tuple[str, str], RetrievedChunk] = {}
        for chunk in vector_results:
            key = (chunk.document_id, chunk.chunk_id)
            vector_map[key] = chunk

        bm25_map: Dict[tuple[str, str], RetrievedChunk] = {}
        for chunk in bm25_results:
            key = (chunk.document_id, chunk.chunk_id)
            bm25_map[key] = chunk

        # Get all unique chunks
        all_keys = set(vector_map.keys()) | set(bm25_map.keys())

        # Normalize scores separately for each method
        vector_scores = [chunk.score for chunk in vector_map.values() if chunk.score is not None]
        bm25_scores = [chunk.score for chunk in bm25_map.values() if chunk.score is not None]

        normalized_vector = self._normalize_scores(vector_scores)
        normalized_bm25 = self._normalize_scores(bm25_scores)

        # Create normalized score maps
        vector_score_map = {
            (chunk.document_id, chunk.chunk_id): score
            for chunk, score in zip(vector_map.values(), normalized_vector)
        }
        bm25_score_map = {
            (chunk.document_id, chunk.chunk_id): score
            for chunk, score in zip(bm25_map.values(), normalized_bm25)
        }

        # Combine scores
        combined: List[RetrievedChunk] = []
        for key in all_keys:
            doc_id, chunk_id = key
            
            # Get normalized scores (default to 0 if not found)
            vector_score = vector_score_map.get(key, 0.0)
            bm25_score = bm25_score_map.get(key, 0.0)
            
            # Weighted combination
            combined_score = (
                self._vector_weight * vector_score +
                self._bm25_weight * bm25_score
            )

            # Get chunk from either map (prefer vector for content)
            chunk = vector_map.get(key) or bm25_map.get(key)
            if chunk:
                combined.append(
                    RetrievedChunk(
                        document_id=chunk.document_id,
                        chunk_id=chunk.chunk_id,
                        content=chunk.content,
                        score=combined_score,
                        metadata=chunk.metadata,
                        rank=0,  # Will be set after sorting
                    )
                )

        # Sort by combined score and assign ranks
        combined.sort(key=lambda c: c.score, reverse=True)
        for idx, chunk in enumerate(combined[:top_k]):
            chunk.rank = idx + 1

        return combined[:top_k]

