"""
ChatController - Infrastructure Layer (HTTP)
Single Responsibility: Handle HTTP requests for chat operations
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.application.usecases.ChatCompletionUseCase import ChatCompletionUseCase
from src.domain.entities.Chat import ChatMessage, ChatSession
from src.domain.repositories.ChatRepository import ChatRepository
from src.infrastructure.database.postgres.models import UserModel
from src.infrastructure.http.dependencies import (
    get_chat_completion_use_case,
    get_chat_repository,
    get_openai_client,
    get_token_tracker,
)
from src.infrastructure.rag.generator.title_generator import TitleGenerator
from src.infrastructure.security.auth import get_current_user

router = APIRouter(prefix="/api/chats", tags=["Chats"])


class ChatSessionResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str

    @classmethod
    def from_entity(cls, session: ChatSession) -> "ChatSessionResponse":
        return cls(
            id=session.id,
            title=session.title,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
        )


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str
    metadata: dict[str, Any] | None = None

    @classmethod
    def from_entity(cls, message: ChatMessage) -> "ChatMessageResponse":
        return cls(
            id=message.id,
            role=message.role,
            content=message.content,
            created_at=message.created_at.isoformat(),
            metadata=message.metadata or {},
        )


class ChatDetailResponse(BaseModel):
    session: ChatSessionResponse
    messages: List[ChatMessageResponse]


class ChatCreateRequest(BaseModel):
    title: Optional[str] = Field(default=None, description="Optional chat title")


class SendMessageRequest(BaseModel):
    content: str
    use_multi_query: bool = True
    use_step_back: bool = False
    group_id: Optional[str] = None


class UpdateChatTitleRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500, description="New chat title")


class SendMessageResponse(BaseModel):
    assistant_message: ChatMessageResponse
    sources: List[str]
    metadata: dict


@router.get("/", response_model=List[ChatSessionResponse])
async def list_chats(
    chat_repository: ChatRepository = Depends(get_chat_repository),
    current_user: UserModel = Depends(get_current_user),
):
    """List chat sessions for current user."""
    sessions = await chat_repository.get_sessions_by_user(str(current_user.id))
    return [ChatSessionResponse.from_entity(session) for session in sessions]


@router.post("/", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    request: ChatCreateRequest,
    chat_repository: ChatRepository = Depends(get_chat_repository),
    current_user: UserModel = Depends(get_current_user),
):
    """Create a new chat session."""
    now = datetime.now(timezone.utc)
    session = ChatSession(
        id=str(uuid4()),
        user_id=str(current_user.id),
        title=request.title or "New Chat",
        created_at=now,
        updated_at=now,
    )
    session = await chat_repository.create_session(session)
    return ChatSessionResponse.from_entity(session)


@router.get("/{chat_id}", response_model=ChatDetailResponse)
async def get_chat(
    chat_id: str,
    chat_repository: ChatRepository = Depends(get_chat_repository),
):
    """Get chat session with messages."""
    session = await chat_repository.get_session(chat_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    messages = await chat_repository.get_messages_by_session(chat_id)
    return ChatDetailResponse(
        session=ChatSessionResponse.from_entity(session),
        messages=[ChatMessageResponse.from_entity(msg) for msg in messages],
    )


@router.post("/{chat_id}/messages", response_model=SendMessageResponse)
async def send_message(
    chat_id: str,
    request: SendMessageRequest,
    chat_repository: ChatRepository = Depends(get_chat_repository),
    chat_completion_use_case: ChatCompletionUseCase = Depends(
        get_chat_completion_use_case
    ),
    token_tracker = Depends(get_token_tracker),
    current_user: UserModel = Depends(get_current_user),
):
    """Send a message and receive assistant response."""
    session = await chat_repository.get_session(chat_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    now = datetime.now(timezone.utc)

    user_message = ChatMessage(
        id=str(uuid4()),
        chat_session_id=chat_id,
        role="user",
        content=request.content,
        created_at=now,
        metadata={},
    )
    await chat_repository.create_message(user_message)

    result = await chat_completion_use_case.execute(
        user_id=str(current_user.id),
        query_text=request.content,
        chat_id=chat_id,
        use_multi_query=request.use_multi_query,
        use_step_back=request.use_step_back,
        group_id=request.group_id,
    )

    assistant_message = ChatMessage(
        id=str(uuid4()),
        chat_session_id=chat_id,
        role="assistant",
        content=result["message"],
        created_at=datetime.now(timezone.utc),
        metadata=result["metadata"],
    )
    assistant_message = await chat_repository.create_message(assistant_message)

    import logging
    logger = logging.getLogger(__name__)
    
    session = await chat_repository.get_session(chat_id)
    logger.info(f"Title generation check: session.title='{session.title if session else 'None'}'")
    
    if session and (session.title == "New Chat" or not session.title or session.title.strip() == ""):
        messages = await chat_repository.get_messages_by_session(chat_id, limit=2)
        logger.info(f"Messages count: {len(messages)}, session.title='{session.title}'")
        
        if len(messages) >= 2:
            user_msg = next((m for m in messages if m.role == "user"), None)
            assistant_msg = next((m for m in messages if m.role == "assistant"), None)
            
            if user_msg and assistant_msg:
                logger.info(f"Generating title for chat {chat_id} from question: {user_msg.content[:50]}...")
                try:
                    openai_client = get_openai_client()
                    title_generator = TitleGenerator(openai_client, token_tracker=token_tracker)
                    generated_title = await title_generator.generate(
                        user_msg.content,
                        assistant_msg.content
                    )
                    logger.info(f"Generated title: '{generated_title}' for chat {chat_id}")
                    updated_session = await chat_repository.update_session(chat_id, generated_title)
                    if updated_session:
                        logger.info(f"Successfully updated session title to: '{updated_session.title}'")
                    else:
                        logger.error(f"Failed to update session title for chat {chat_id}")
                except Exception as e:
                    logger.error(f"Error generating title for chat {chat_id}: {e}", exc_info=True)
            else:
                logger.warning(f"Could not find user or assistant message in messages list")
        else:
            logger.warning(f"Not enough messages to generate title: {len(messages)} < 2")
    else:
        logger.info(f"Skipping title generation: session.title='{session.title if session else 'None'}'")

    return SendMessageResponse(
        assistant_message=ChatMessageResponse.from_entity(assistant_message),
        sources=result["sources"],
        metadata=result["metadata"],
    )


@router.patch("/{chat_id}", response_model=ChatSessionResponse)
async def update_chat_title(
    chat_id: str,
    request: UpdateChatTitleRequest,
    chat_repository: ChatRepository = Depends(get_chat_repository),
    current_user: UserModel = Depends(get_current_user),
):
    """Update chat session title."""
    session = await chat_repository.get_session(chat_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    
    if str(session.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    updated_session = await chat_repository.update_session(chat_id, request.title)
    if not updated_session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    
    return ChatSessionResponse.from_entity(updated_session)


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: str,
    chat_repository: ChatRepository = Depends(get_chat_repository),
    current_user: UserModel = Depends(get_current_user),
):
    """Delete a chat session."""
    session = await chat_repository.get_session(chat_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    
    if str(session.user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    deleted = await chat_repository.delete_session(chat_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    
    return None

