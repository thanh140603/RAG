"""
ChatRepository interface - Domain Layer
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.Chat import ChatSession, ChatMessage


class ChatRepository(ABC):
    # Chat sessions
    @abstractmethod
    async def create_session(self, session: ChatSession) -> ChatSession:
        raise NotImplementedError

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        raise NotImplementedError

    @abstractmethod
    async def get_sessions_by_user(self, user_id: str) -> List[ChatSession]:
        raise NotImplementedError

    @abstractmethod
    async def update_session(self, session_id: str, title: str) -> Optional[ChatSession]:
        raise NotImplementedError

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        raise NotImplementedError

    # Chat messages
    @abstractmethod
    async def create_message(self, message: ChatMessage) -> ChatMessage:
        raise NotImplementedError

    @abstractmethod
    async def get_messages_by_session(
        self, session_id: str, limit: int = 100
    ) -> List[ChatMessage]:
        raise NotImplementedError

