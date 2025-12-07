"""
Auth & Authorization helpers using JWT.
"""
from __future__ import annotations

import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import get_settings
from src.infrastructure.database.postgres.connection import get_db
from src.infrastructure.database.postgres.models import UserModel

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_password_hash(password: str) -> str:
    """
    Hash password with bcrypt.
    Bcrypt has a 72-byte limit, so we truncate if necessary.
    Uses bcrypt directly to avoid passlib initialization issues.
    """
    # Convert to bytes and truncate to 72 bytes max
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Hash with bcrypt (returns bytes, decode to string for storage)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against bcrypt hash.
    """
    # Convert to bytes and truncate to 72 bytes max (must match hash behavior)
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Verify with bcrypt
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def _create_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    to_encode.update({"iat": now.timestamp(), "exp": expire.timestamp()})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def create_access_token(user: UserModel) -> str:
    claims = {
        "sub": str(user.id),
        "role": user.role,
        "type": "access",
    }
    expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    return _create_token(claims, expires)


def create_refresh_token(user: UserModel) -> str:
    claims = {
        "sub": str(user.id),
        "role": user.role,
        "type": "refresh",
    }
    expires = timedelta(days=settings.jwt_refresh_token_expire_days)
    return _create_token(claims, expires)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    stmt = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


async def get_current_admin(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


