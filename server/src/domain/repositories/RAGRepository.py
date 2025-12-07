"""
RAGRepository Interface - Domain Layer
Interface Segregation: Specific interface for RAG operations
"""
from abc import ABC, abstractmethod
from typing import List
from src.domain.entities.RetrievedChunk import RetrievedChunk
from src.domain.entities.UserQuery import UserQuery


class RAGRepository(ABC):
    """
    RAG Repository Interface
    Single Responsibility: Define contract for RAG retrieval operations
    """
    
    @abstractmethod
    async def retrieve(
        self, 
        query: UserQuery,
        top_k: int = 5
    ) -> List[RetrievedChunk]:
        """
        Retrieve relevant chunks for a query
        Open/Closed: Can be extended with different retrieval strategies
        """
        # TODO: Implement retrieval logic
        pass
    
    @abstractmethod
    async def retrieve_multi_query(
        self,
        queries: List[str],
        top_k: int = 5
    ) -> List[RetrievedChunk]:
        """Retrieve chunks for multiple query variations"""
        # TODO: Implement multi-query retrieval
        pass

