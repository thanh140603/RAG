"""
ChatRepositoryImpl - Infrastructure Layer
"""
from __future__ import annotations

from typing import List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.Chat import ChatSession, ChatMessage
from src.domain.repositories.ChatRepository import ChatRepository
from src.infrastructure.database.postgres.mappers import (
    ChatSessionMapper,
    ChatMessageMapper,
)
from src.infrastructure.database.postgres.models import ChatSessionModel, ChatMessageModel


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


class ChatRepositoryImpl(ChatRepository):
    def __init__(self, db_session: AsyncSession):
        self._db = db_session

    async def create_session(self, session: ChatSession) -> ChatSession:
        model = ChatSessionMapper.to_model(session)
        self._db.add(model)
        await self._db.flush()
        await self._db.refresh(model)
        return ChatSessionMapper.to_entity(model)

    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        session_uuid = _uuid(session_id)
        if session_uuid is None:
            return None
        stmt = select(ChatSessionModel).where(
            ChatSessionModel.id == session_uuid
        )
        result = await self._db.execute(stmt)
        model = result.scalar_one_or_none()
        return ChatSessionMapper.to_entity(model) if model else None

    async def get_sessions_by_user(self, user_id: str) -> List[ChatSession]:
        user_uuid = _uuid(user_id)
        if user_uuid is None:
            return []
        stmt = (
            select(ChatSessionModel)
            .where(ChatSessionModel.user_id == user_uuid)
            .order_by(ChatSessionModel.updated_at.desc())
        )
        result = await self._db.execute(stmt)
        models = result.scalars().all()
        return [ChatSessionMapper.to_entity(model) for model in models]

    async def update_session(self, session_id: str, title: str) -> Optional[ChatSession]:
        session_uuid = _uuid(session_id)
        if session_uuid is None:
            return None
        stmt = select(ChatSessionModel).where(ChatSessionModel.id == session_uuid)
        result = await self._db.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        model.title = title
        await self._db.flush()
        await self._db.refresh(model)
        return ChatSessionMapper.to_entity(model)

    async def delete_session(self, session_id: str) -> bool:
        session_uuid = _uuid(session_id)
        if session_uuid is None:
            return False
        stmt = select(ChatSessionModel).where(ChatSessionModel.id == session_uuid)
        result = await self._db.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return False
        await self._db.delete(model)
        await self._db.flush()
        return True

    async def create_message(self, message: ChatMessage) -> ChatMessage:
        model = ChatMessageMapper.to_model(message)
        self._db.add(model)
        await self._db.flush()
        await self._db.refresh(model)
        return ChatMessageMapper.to_entity(model)

    async def get_messages_by_session(
        self, session_id: str, limit: int = 100
    ) -> List[ChatMessage]:
        session_uuid = _uuid(session_id)
        if session_uuid is None:
            return []
        stmt = (
            select(ChatMessageModel)
            .where(ChatMessageModel.session_id == session_uuid)  # Model attribute is session_id, maps to chat_session_id column
            .order_by(ChatMessageModel.created_at.asc())
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        models = result.scalars().all()
        return [ChatMessageMapper.to_entity(model) for model in models]