"""
ApiTokenUsageRepository interface - Domain Layer
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from src.domain.entities.ApiTokenUsage import ApiTokenUsage


class ApiTokenUsageRepository(ABC):
    @abstractmethod
    async def create_or_update(
        self, 
        provider: str, 
        date: datetime, 
        tokens_used: int, 
        requests_count: int = 1
    ) -> ApiTokenUsage:
        """Create or update token usage for a provider on a specific date."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_provider_and_date(
        self, provider: str, date: datetime
    ) -> Optional[ApiTokenUsage]:
        """Get token usage for a provider on a specific date."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_provider_date_range(
        self, provider: str, start_date: datetime, end_date: datetime
    ) -> List[ApiTokenUsage]:
        """Get token usage for a provider within a date range."""
        raise NotImplementedError

    @abstractmethod
    async def set_limits(
        self, provider: str, daily_limit: Optional[int] = None, monthly_limit: Optional[int] = None
    ) -> bool:
        """Set daily/monthly limits for a provider (applies to all dates)."""
        raise NotImplementedError

    @abstractmethod
    async def get_all_providers(self) -> List[str]:
        """Get list of all providers that have usage records."""
        raise NotImplementedError

