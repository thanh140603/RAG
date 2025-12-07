"""
Embedding Entity - Domain Layer
Single Responsibility: Represents a text embedding vector
"""
from dataclasses import dataclass, field
from typing import List
from datetime import datetime


@dataclass
class Embedding:
    """
    Embedding entity - Vector representation of text
    Immutable value object
    """
    id: str
    document_id: str
    chunk_id: str
    text: str
    vector: List[float]
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def dimension(self) -> int:
        """Get embedding dimension"""
        return len(self.vector)
    
    def is_valid(self) -> bool:
        """Validate embedding vector"""
        return len(self.vector) > 0 and all(isinstance(x, (int, float)) for x in self.vector)

