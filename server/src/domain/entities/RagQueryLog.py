"""
RagQueryLog Entity - Domain Layer
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class RagQueryLog:
    id: str
    query_text: str
    user_id: Optional[str]
    chat_message_id: Optional[str]
    use_multi_query: bool
    use_step_back: bool
    top_k: int
    status: str
    options: Optional[Dict[str, Any]] = None
    translated_query: Optional[str] = None
    step_back_query: Optional[str] = None
    response_latency_ms: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

