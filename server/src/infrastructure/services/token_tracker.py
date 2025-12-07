"""
TokenTracker - Infrastructure Layer
Single Responsibility: Track API token usage
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

from src.domain.repositories.ApiTokenUsageRepository import ApiTokenUsageRepository


class TokenTracker:
    """Service to track API token usage"""
    
    def __init__(self, token_repository: ApiTokenUsageRepository):
        self._token_repository = token_repository
    
    async def track_usage(
        self,
        provider: str,
        tokens_used: int,
        requests_count: int = 1,
        date: Optional[datetime] = None
    ) -> None:
        """
        Track token usage for a provider.
        
        Args:
            provider: API provider name (e.g., 'groq', 'tavily')
            tokens_used: Number of tokens used
            requests_count: Number of requests (default: 1)
            date: Date to track (default: now)
        """
        if date is None:
            date = datetime.now()
        
        try:
            await self._token_repository.create_or_update(
                provider=provider,
                date=date,
                tokens_used=tokens_used,
                requests_count=requests_count
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to track token usage for {provider}: {e}", exc_info=True)
    
    async def track_usage_async(
        self,
        provider: str,
        tokens_used: int,
        requests_count: int = 1,
        date: Optional[datetime] = None
    ) -> None:
        """Track token usage asynchronously (fire and forget)."""
        asyncio.create_task(self.track_usage(provider, tokens_used, requests_count, date))

