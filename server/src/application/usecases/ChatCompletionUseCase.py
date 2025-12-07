"""
ChatCompletionUseCase - Application Layer
Single Responsibility: Handle chat completion workflow
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, List
from uuid import uuid4

from src.config.settings import get_settings
from src.application.usecases.QueryRAGUseCase import QueryRAGUseCase
from src.domain.entities.UserQuery import UserQuery
from src.domain.entities.Chat import ChatMessage
from src.domain.repositories.ChatRepository import ChatRepository

settings = get_settings()
logger = logging.getLogger(__name__)


class ChatCompletionUseCase:
    """
    Use Case: Generate chat completion with RAG
    Single Responsibility: Handle chat completion business logic
    """

    def __init__(
        self, 
        query_rag_use_case: QueryRAGUseCase,
        chat_repository: Optional[ChatRepository] = None,
    ):
        self._query_rag_use_case = query_rag_use_case
        self._chat_repository = chat_repository

    def _is_follow_up_question(self, query_text: str) -> bool:
        """
        Detect if query is a follow-up question (e.g., "more details", "above question", "tell me more")
        """
        follow_up_indicators = [
            "more details",
            "above question",
            "tell me more",
            "what about",
            "and",
            "also",
            "how about",
            "can you explain",
            "elaborate",
            "expand",
        ]
        query_lower = query_text.lower()
        return any(indicator in query_lower for indicator in follow_up_indicators)

    def _expand_query_with_context(
        self, 
        query_text: str, 
        conversation_history: List[ChatMessage]
    ) -> str:
        """
        Expand follow-up questions with context from conversation history
        """
        if not self._is_follow_up_question(query_text):
            return query_text

        # Get last user question and assistant response
        last_user_question = None
        last_assistant_response = None
        
        for msg in reversed(conversation_history):
            if msg.role == "user" and last_user_question is None:
                last_user_question = msg.content
            elif msg.role == "assistant" and last_assistant_response is None:
                last_assistant_response = msg.content
            if last_user_question and last_assistant_response:
                break

        # Expand query with context
        if last_user_question and last_assistant_response:
            expanded = f"{last_user_question}. {query_text}. Context from previous answer: {last_assistant_response[:200]}"
            logger.info(f"Expanded follow-up question: {query_text} -> {expanded[:100]}...")
            return expanded
        
        return query_text

    async def execute(
        self,
        user_id: str,
        query_text: str,
        chat_id: Optional[str] = None,
        use_multi_query: bool = True,
        use_step_back: bool = False,
        top_k: Optional[int] = None,
        group_id: Optional[str] = None,
    ) -> dict:
        """
        Execute chat completion with conversation history support
        """
        # Load conversation history if chat_id is provided
        conversation_history: List[ChatMessage] = []
        if chat_id and self._chat_repository:
            conversation_history = await self._chat_repository.get_messages_by_session(
                chat_id, limit=10  # Last 10 messages for context
            )
            logger.info(f"Loaded {len(conversation_history)} messages from conversation history")

        # Expand query if it's a follow-up question
        expanded_query = query_text
        if conversation_history and self._is_follow_up_question(query_text):
            expanded_query = self._expand_query_with_context(query_text, conversation_history)

        query = UserQuery(
            id=str(uuid4()),
            user_id=user_id,
            chat_id=chat_id,
            query_text=expanded_query,  # Use expanded query
            created_at=datetime.now(timezone.utc),
            use_multi_query=use_multi_query,
            use_step_back=use_step_back,
            group_id=group_id,
        )

        result = await self._query_rag_use_case.execute(
            query,
            top_k=top_k or settings.top_k,
            conversation_history=conversation_history,  # Pass history to RAG
        )

        logger.info(
            "Chat completion generated user=%s chat=%s retrieved=%d",
            user_id,
            chat_id,
            len(result["retrieved_chunks"]),
        )

        return {
            "message": result["answer"],
            "sources": [chunk.document_id for chunk in result["retrieved_chunks"]],
            "metadata": {
                "query_variations": result["query_variations"],
                "step_back_query": result.get("step_back_query"),
                "retrieved_count": len(result["retrieved_chunks"]),
            },
        }
