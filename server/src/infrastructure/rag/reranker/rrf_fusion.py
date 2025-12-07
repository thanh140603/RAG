"""
RRFFusion - Infrastructure Layer
Single Responsibility: Fuse and rerank results using RRF
"""
from typing import Dict, List, Tuple
from src.domain.entities.RetrievedChunk import RetrievedChunk


class RRFFusion:
    """
    Reciprocal Rank Fusion (RRF) reranker
    Single Responsibility: Fuse multiple result sets using RRF
    """
    
    def __init__(self, k: int = 60):
        """
        Initialize RRF with constant k
        k=60 is standard value
        """
        self.k = k
    
    async def fuse(
        self,
        result_sets: List[List[RetrievedChunk]],
        top_k: int = 5
    ) -> List[RetrievedChunk]:
        """
        Fuse multiple result sets using RRF algorithm
        """
        if not result_sets:
            return []

        aggregated: Dict[Tuple[str, str], dict] = {}
        for results in result_sets:
            for idx, chunk in enumerate(results):
                rank = chunk.rank if chunk.rank and chunk.rank > 0 else idx + 1
                score = self._calculate_rrf_score(rank)
                key = (chunk.document_id, chunk.chunk_id)

                if key not in aggregated:
                    aggregated[key] = {
                        "chunk": chunk,
                        "score": 0.0,
                    }

                aggregated[key]["score"] += score

        fused: List[RetrievedChunk] = []
        for _, data in aggregated.items():
            chunk = data["chunk"]
            fused.append(
                RetrievedChunk(
                    document_id=chunk.document_id,
                    chunk_id=chunk.chunk_id,
                    content=chunk.content,
                    score=data["score"],
                    metadata=chunk.metadata,
                )
            )

        fused.sort(key=lambda c: c.score, reverse=True)
        for rank, chunk in enumerate(fused[:top_k], start=1):
            chunk.rank = rank
        return fused[:top_k]
    
    def _calculate_rrf_score(self, rank: int) -> float:
        """Calculate RRF score for a rank"""
        return 1.0 / (self.k + rank)

