"""
ApiTokenUsage entity - Domain Layer
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class ApiTokenUsage:
    id: str
    provider: str  # 'groq', 'tavily', etc.
    date: datetime
    tokens_used: int
    requests_count: int
    daily_limit: Optional[int] = None
    monthly_limit: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

