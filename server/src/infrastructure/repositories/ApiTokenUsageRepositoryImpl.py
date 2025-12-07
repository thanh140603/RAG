"""
ApiTokenUsageRepositoryImpl - Infrastructure Layer
"""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime, date
import uuid

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.ApiTokenUsage import ApiTokenUsage
from src.domain.repositories.ApiTokenUsageRepository import ApiTokenUsageRepository
from src.infrastructure.database.postgres.mappers import ApiTokenUsageMapper
from src.infrastructure.database.postgres.models import ApiTokenUsageModel


def _uuid(value: str | uuid.UUID | None) -> uuid.UUID | None:
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    if isinstance(value, str) and not value.strip():
        return None
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        return None


class ApiTokenUsageRepositoryImpl(ApiTokenUsageRepository):
    def __init__(self, db_session: AsyncSession):
        self._db = db_session

    async def create_or_update(
        self, 
        provider: str, 
        date: datetime, 
        tokens_used: int, 
        requests_count: int = 1
    ) -> ApiTokenUsage:
        """Create or update token usage for a provider on a specific date."""
        date_start = datetime.combine(date.date(), datetime.min.time()).replace(tzinfo=date.tzinfo)
        
        stmt = select(ApiTokenUsageModel).where(
            and_(
                ApiTokenUsageModel.provider == provider,
                func.date(ApiTokenUsageModel.date) == date_start.date()
            )
        )
        result = await self._db.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            model.tokens_used += tokens_used
            model.requests_count += requests_count
            from datetime import timezone as tz
            model.updated_at = datetime.now(tz.utc if date.tzinfo else None)
        else:
            model = ApiTokenUsageModel(
                provider=provider,
                date=date_start,
                tokens_used=tokens_used,
                requests_count=requests_count,
            )
            self._db.add(model)
        
        await self._db.flush()
        await self._db.refresh(model)
        return ApiTokenUsageMapper.to_entity(model)

    async def get_by_provider_and_date(
        self, provider: str, date: datetime
    ) -> Optional[ApiTokenUsage]:
        """Get token usage for a provider on a specific date."""
        from datetime import time as dt_time
        date_start = datetime.combine(date.date(), dt_time.min).replace(tzinfo=date.tzinfo if date.tzinfo else None)
        
        stmt = select(ApiTokenUsageModel).where(
            and_(
                ApiTokenUsageModel.provider == provider,
                func.date(ApiTokenUsageModel.date) == date_start.date()
            )
        )
        result = await self._db.execute(stmt)
        model = result.scalar_one_or_none()
        return ApiTokenUsageMapper.to_entity(model) if model else None

    async def get_by_provider_date_range(
        self, provider: str, start_date: datetime, end_date: datetime
    ) -> List[ApiTokenUsage]:
        """Get token usage for a provider within a date range."""
        stmt = (
            select(ApiTokenUsageModel)
            .where(
                and_(
                    ApiTokenUsageModel.provider == provider,
                    ApiTokenUsageModel.date >= start_date,
                    ApiTokenUsageModel.date <= end_date
                )
            )
            .order_by(ApiTokenUsageModel.date.asc())
        )
        result = await self._db.execute(stmt)
        models = result.scalars().all()
        return [ApiTokenUsageMapper.to_entity(model) for model in models]

    async def set_limits(
        self, provider: str, daily_limit: Optional[int] = None, monthly_limit: Optional[int] = None
    ) -> bool:
        """Set daily/monthly limits for a provider (updates all records for this provider)."""
        stmt = select(ApiTokenUsageModel).where(ApiTokenUsageModel.provider == provider)
        result = await self._db.execute(stmt)
        models = result.scalars().all()
        
        if not models:
            return False
        
        for model in models:
            if daily_limit is not None:
                model.daily_limit = daily_limit
            if monthly_limit is not None:
                model.monthly_limit = monthly_limit
            model.updated_at = datetime.now(model.date.tzinfo)
        
        await self._db.flush()
        return True

    async def get_all_providers(self) -> List[str]:
        """Get list of all providers that have usage records."""
        stmt = select(ApiTokenUsageModel.provider).distinct()
        result = await self._db.execute(stmt)
        providers = [row[0] for row in result.all()]
        # If no providers exist, return empty list (will show empty state in UI)
        return providers

