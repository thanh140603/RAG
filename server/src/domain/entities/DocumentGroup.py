"""
DocumentGroup Entity - Domain Layer
Single Responsibility: Represents a document group in the domain
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class DocumentGroup:
    """
    DocumentGroup entity - Core domain model
    Represents a collection/group of related documents
    """
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    color: Optional[str] = None  # Hex color for UI (e.g., "#3B82F6")
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

