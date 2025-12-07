"""
Chat entities - Domain Layer
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class ChatSession:
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime


@dataclass
class ChatMessage:
    id: str
    chat_session_id: str
    role: str  # user | assistant | system
    content: str
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    rag_query_id: Optional[str] = None

