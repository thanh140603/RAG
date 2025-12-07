"""
Chunk Entity - Domain Layer
Represents a chunk of a document
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class Chunk:
    id: str
    document_id: str
    order: int
    text: str
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

