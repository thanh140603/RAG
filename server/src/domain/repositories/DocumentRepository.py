"""
DocumentRepository Interface - Domain Layer
Interface Segregation: Specific interface for document operations
Dependency Inversion: Domain depends on abstraction, not implementation
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.Document import Document, DocumentStatus


class DocumentRepository(ABC):
    """
    Document Repository Interface
    Single Responsibility: Define contract for document persistence
    """
    
    @abstractmethod
    async def create(self, document: Document) -> Document:
        """Create a new document"""
        # TODO: Implement document creation
        pass
    
    @abstractmethod
    async def get_by_id(self, document_id: str) -> Optional[Document]:
        """Get document by ID"""
        # TODO: Implement document retrieval by ID
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> List[Document]:
        """Get all documents for a user"""
        # TODO: Implement document retrieval by user
        pass
    
    @abstractmethod
    async def update_status(
        self, 
        document_id: str, 
        status: DocumentStatus,
        **kwargs
    ) -> Document:
        """Update document status"""
        # TODO: Implement status update
        pass
    
    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """Delete a document"""
        # TODO: Implement document deletion
        pass
    
    @abstractmethod
    async def exists(self, document_id: str) -> bool:
        """Check if document exists"""
        # TODO: Implement existence check
        pass

    @abstractmethod
    async def update_file_info(
        self,
        document_id: str,
        *,
        file_size: int | None = None,
        metadata: Optional[dict] = None,
    ) -> Document:
        """Update document file metadata/info"""
        pass

