"""
ChunkRepository interface - Domain Layer
"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from src.domain.entities.Chunk import Chunk


class ChunkRepository(ABC):
    @abstractmethod
    async def create_many(self, chunks: List[Chunk]) -> List[Chunk]:
        """Persist a batch of chunks for a document"""
        raise NotImplementedError

    @abstractmethod
    async def get_by_document_id(self, document_id: str) -> List[Chunk]:
        """Fetch chunks for a given document"""
        raise NotImplementedError

    @abstractmethod
    async def delete_by_document_id(self, document_id: str) -> None:
        """Remove all chunks associated with a document"""
        raise NotImplementedError

    @abstractmethod
    async def search_bm25(
        self,
        query: str,
        top_k: int = 5,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
    ) -> List[Tuple[Chunk, float]]:
        """
        Search chunks using BM25 algorithm
        Returns list of (chunk, bm25_score) tuples
        """
        raise NotImplementedError

