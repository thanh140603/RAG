"""
DocumentGroupRepository Interface - Domain Layer
Interface Segregation: Specific interface for document group operations
Dependency Inversion: Domain depends on abstraction, not implementation
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.entities.DocumentGroup import DocumentGroup


class DocumentGroupRepository(ABC):
    """
    DocumentGroup Repository Interface
    Single Responsibility: Define contract for document group persistence
    """
    
    @abstractmethod
    async def create(self, group: DocumentGroup) -> DocumentGroup:
        """Create a new document group"""
        pass
    
    @abstractmethod
    async def get_by_id(self, group_id: str) -> Optional[DocumentGroup]:
        """Get group by ID"""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> List[DocumentGroup]:
        """Get all groups for a user"""
        pass
    
    @abstractmethod
    async def update(self, group: DocumentGroup) -> DocumentGroup:
        """Update a document group"""
        pass
    
    @abstractmethod
    async def delete(self, group_id: str) -> bool:
        """Delete a document group"""
        pass
    
    @abstractmethod
    async def exists(self, group_id: str) -> bool:
        """Check if group exists"""
        pass

