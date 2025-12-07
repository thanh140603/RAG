"""
RAGController - Infrastructure Layer (HTTP)
Single Responsibility: Handle HTTP requests for RAG operations
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from src.application.usecases.ChatCompletionUseCase import ChatCompletionUseCase
from src.infrastructure.database.postgres.models import UserModel
from src.infrastructure.http.dependencies import get_chat_completion_use_case
from src.infrastructure.security.auth import get_current_user

router = APIRouter(prefix="/api/rag", tags=["RAG"])


class QueryRequest(BaseModel):
    query: str
    chat_id: Optional[str] = None
    use_multi_query: bool = True
    use_step_back: bool = False
    group_id: Optional[str] = None  # Filter by document group


class QueryResponse(BaseModel):
    message: str
    sources: list[str]
    metadata: dict


@router.post("/query", response_model=QueryResponse)
async def query_rag(
    request: QueryRequest,
    use_case: ChatCompletionUseCase = Depends(get_chat_completion_use_case),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Query RAG system
    """
    try:
        result = await use_case.execute(
            user_id=str(current_user.id),
            query_text=request.query,
            chat_id=request.chat_id,
            use_multi_query=request.use_multi_query,
            use_step_back=request.use_step_back,
            group_id=request.group_id,
        )
        
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

