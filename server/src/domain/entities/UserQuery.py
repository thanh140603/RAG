"""
UserQuery Entity - Domain Layer
Single Responsibility: Represents a user query
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class UserQuery:
    """
    UserQuery entity - Represents a query from user
    Immutable value object
    """
    id: str
    user_id: str
    chat_id: Optional[str]
    query_text: str
    created_at: datetime
    query_variations: Optional[List[str]] = None
    use_multi_query: bool = True
    use_step_back: bool = False
    group_id: Optional[str] = None  # Filter by document group
    
    def has_variations(self) -> bool:
        """Check if query has variations"""
        return self.query_variations is not None and len(self.query_variations) > 0

