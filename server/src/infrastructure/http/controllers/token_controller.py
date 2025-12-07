"""
TokenController - Infrastructure Layer (HTTP)
Single Responsibility: Handle HTTP requests for API token usage tracking
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.domain.repositories.ApiTokenUsageRepository import ApiTokenUsageRepository
from src.infrastructure.database.postgres.models import UserModel
from src.infrastructure.http.dependencies import get_api_token_usage_repository
from src.infrastructure.security.auth import get_current_user

router = APIRouter(prefix="/api/tokens", tags=["Tokens"])


class TokenUsageResponse(BaseModel):
    id: str
    provider: str
    date: str
    tokens_used: int
    requests_count: int
    daily_limit: Optional[int] = None
    monthly_limit: Optional[int] = None
    metadata: dict = {}

    @classmethod
    def from_entity(cls, usage) -> "TokenUsageResponse":
        return cls(
            id=usage.id,
            provider=usage.provider,
            date=usage.date.isoformat(),
            tokens_used=usage.tokens_used,
            requests_count=usage.requests_count,
            daily_limit=usage.daily_limit,
            monthly_limit=usage.monthly_limit,
            metadata=usage.metadata or {},
        )


class TokenUsageSummaryResponse(BaseModel):
    provider: str
    today_tokens: int
    today_requests: int
    month_tokens: int
    month_requests: int
    daily_limit: Optional[int] = None
    monthly_limit: Optional[int] = None
    daily_percentage: float = 0.0
    monthly_percentage: float = 0.0


class SetLimitsRequest(BaseModel):
    daily_limit: Optional[int] = Field(None, ge=0, description="Daily token limit")
    monthly_limit: Optional[int] = Field(None, ge=0, description="Monthly token limit")


def _check_admin(user: UserModel) -> None:
    """Check if user is admin."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access token usage"
        )


@router.get("/summary", response_model=List[TokenUsageSummaryResponse])
async def get_token_usage_summary(
    token_repository: ApiTokenUsageRepository = Depends(get_api_token_usage_repository),
    current_user: UserModel = Depends(get_current_user),
):
    """Get token usage summary for all providers (admin only)."""
    _check_admin(current_user)
    
    providers = await token_repository.get_all_providers()
    if not providers:
        return []
    
    now = datetime.now()
    from datetime import time as dt_time
    today_start = datetime.combine(now.date(), dt_time.min).replace(tzinfo=now.tzinfo if now.tzinfo else None)
    month_start = (now.replace(day=1) - timedelta(days=0)).replace(hour=0, minute=0, second=0, microsecond=0)
    if now.tzinfo:
        month_start = month_start.replace(tzinfo=now.tzinfo)
    
    summaries = []
    for provider in providers:
        today_usage = await token_repository.get_by_provider_and_date(provider, now)
        month_usages = await token_repository.get_by_provider_date_range(provider, month_start, now)
        
        today_tokens = today_usage.tokens_used if today_usage else 0
        today_requests = today_usage.requests_count if today_usage else 0
        month_tokens = sum(u.tokens_used for u in month_usages)
        month_requests = sum(u.requests_count for u in month_usages)
        
        daily_limit = today_usage.daily_limit if today_usage else None
        monthly_limit = today_usage.monthly_limit if today_usage else None
        
        daily_percentage = (today_tokens / daily_limit * 100) if daily_limit and daily_limit > 0 else 0.0
        monthly_percentage = (month_tokens / monthly_limit * 100) if monthly_limit and monthly_limit > 0 else 0.0
        
        summaries.append(TokenUsageSummaryResponse(
            provider=provider,
            today_tokens=today_tokens,
            today_requests=today_requests,
            month_tokens=month_tokens,
            month_requests=month_requests,
            daily_limit=daily_limit,
            monthly_limit=monthly_limit,
            daily_percentage=round(daily_percentage, 2),
            monthly_percentage=round(monthly_percentage, 2),
        ))
    
    return summaries


@router.get("/usage", response_model=List[TokenUsageResponse])
async def get_token_usage(
    provider: Optional[str] = None,
    days: int = 30,
    token_repository: ApiTokenUsageRepository = Depends(get_api_token_usage_repository),
    current_user: UserModel = Depends(get_current_user),
):
    """Get token usage history (admin only)."""
    _check_admin(current_user)
    
    now = datetime.now()
    start_date = now - timedelta(days=days)
    
    if provider:
        usages = await token_repository.get_by_provider_date_range(provider, start_date, now)
    else:
        providers = await token_repository.get_all_providers()
        all_usages = []
        for p in providers:
            usages = await token_repository.get_by_provider_date_range(p, start_date, now)
            all_usages.extend(usages)
        usages = sorted(all_usages, key=lambda x: x.date, reverse=True)
    
    return [TokenUsageResponse.from_entity(u) for u in usages]


@router.post("/limits/{provider}", response_model=dict)
async def set_token_limits(
    provider: str,
    request: SetLimitsRequest,
    token_repository: ApiTokenUsageRepository = Depends(get_api_token_usage_repository),
    current_user: UserModel = Depends(get_current_user),
):
    """Set token limits for a provider (admin only)."""
    _check_admin(current_user)
    
    success = await token_repository.set_limits(
        provider,
        daily_limit=request.daily_limit,
        monthly_limit=request.monthly_limit
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No usage records found for provider: {provider}"
        )
    
    return {"message": "Limits updated successfully", "provider": provider}

