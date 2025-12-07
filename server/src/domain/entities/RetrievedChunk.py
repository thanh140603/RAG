"""
RetrievedChunk Entity - Domain Layer
Single Responsibility: Represents a retrieved document chunk
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class RetrievedChunk:
    """
    RetrievedChunk entity - Represents a chunk retrieved from vector store
    Immutable value object
    """
    document_id: str
    chunk_id: str
    content: str
    score: float
    metadata: dict
    rank: Optional[int] = None
    
    def is_relevant(self, threshold: float = 0.5) -> bool:
        """Check if chunk is relevant based on score threshold"""
        return self.score >= threshold

