"""
EmbeddingRepository Interface - Domain Layer
Interface Segregation: Specific interface for embedding operations
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from src.domain.entities.Embedding import Embedding


class EmbeddingRepository(ABC):
    """
    Embedding Repository Interface
    Single Responsibility: Define contract for embedding persistence
    """
    
    @abstractmethod
    async def create(self, embedding: Embedding) -> Embedding:
        """Create a new embedding"""
        # TODO: Implement embedding creation
        pass
    
    @abstractmethod
    async def create_batch(self, embeddings: List[Embedding]) -> List[Embedding]:
        """Create multiple embeddings"""
        # TODO: Implement batch embedding creation
        pass
    
    @abstractmethod
    async def get_by_document_id(self, document_id: str) -> List[Embedding]:
        """Get all embeddings for a document"""
        # TODO: Implement retrieval by document
        pass
    
    @abstractmethod
    async def delete_by_document_id(self, document_id: str) -> bool:
        """Delete all embeddings for a document"""
        # TODO: Implement deletion by document
        pass
    
    @abstractmethod
    async def search_similar(
        self, 
        query_vector: List[float], 
        top_k: int = 5,
        filter_metadata: Optional[dict] = None,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
    ) -> List[Tuple[Embedding, float]]:
        """Search for similar embeddings"""
        # TODO: Implement vector similarity search
        pass

