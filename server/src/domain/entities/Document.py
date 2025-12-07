"""
Document Entity - Domain Layer
Single Responsibility: Represents a document in the domain
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict
from enum import Enum


class DocumentStatus(str, Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    ERROR = "error"


@dataclass
class Document:
    """
    Document entity - Core domain model
    Immutable value object representing a document
    """
    id: str
    user_id: str
    filename: str
    file_type: str
    file_size: int
    status: DocumentStatus
    uploaded_at: datetime
    indexed_at: Optional[datetime] = None
    chunk_count: Optional[int] = None
    embedding_model: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None
    storage_key: Optional[str] = None
    checksum: Optional[str] = None
    group_id: Optional[str] = None
    
    def is_indexed(self) -> bool:
        """Check if document is indexed"""
        return self.status == DocumentStatus.INDEXED
    
    def can_be_queried(self) -> bool:
        """Check if document can be used for queries"""
        return self.is_indexed() and self.chunk_count is not None and self.chunk_count > 0

