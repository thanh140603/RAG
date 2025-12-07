"""
AuthController - handle registration, login, and current user info.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import get_settings
from src.infrastructure.database.postgres.connection import get_db
from src.infrastructure.database.postgres.models import UserModel
from src.infrastructure.security.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_password_hash,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])

settings = get_settings()


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: Optional[str] = "user"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: str

    @classmethod
    def from_model(cls, user: UserModel) -> "UserResponse":
        return cls(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role,
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    stmt = select(UserModel).where(UserModel.email == payload.email)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    now = datetime.now(timezone.utc)
    user = UserModel(
        email=payload.email,
        name=payload.name,
        hashed_password=get_password_hash(payload.password),
        role=payload.role or "user",
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return UserResponse.from_model(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return JWT tokens."""
    stmt = select(UserModel).where(UserModel.email == payload.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: UserModel = Depends(get_current_user)):
    """Return current authenticated user."""
    return UserResponse.from_model(current_user)


