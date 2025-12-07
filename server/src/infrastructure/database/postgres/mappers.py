"""
Mappers - Convert between Domain Entities and Database Models
Single Responsibility: Handle entity-model conversions
"""
from __future__ import annotations

import uuid
from typing import Optional

from src.domain.entities.Document import Document
from src.domain.entities.DocumentGroup import DocumentGroup
from src.domain.entities.Embedding import Embedding
from src.domain.entities.Chunk import Chunk
from src.domain.entities.Chat import ChatSession, ChatMessage
from src.domain.entities.RagQueryLog import RagQueryLog
from src.domain.entities.RetrievedChunk import RetrievedChunk
from src.domain.entities.ApiTokenUsage import ApiTokenUsage
from src.infrastructure.database.postgres.models import (
    DocumentModel,
    DocumentGroupModel,
    EmbeddingModel,
    ChunkModel,
    ChatSessionModel,
    ChatMessageModel,
    RagQueryModel,
    RagRetrievedChunkModel,
    RagQueryStatus,
    ApiTokenUsageModel,
)


def _uuid(value: str | uuid.UUID | None) -> Optional[uuid.UUID]:
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


class DocumentMapper:
    """Mapper for Document entity <-> DocumentModel"""
    
    @staticmethod
    def to_entity(model: DocumentModel) -> Document:
        """Convert DocumentModel to Domain Entity"""
        return Document(
            id=str(model.id),
            user_id=str(model.user_id),
            filename=model.filename,
            file_type=model.file_type,
            file_size=model.file_size,
            status=model.status,
            uploaded_at=model.uploaded_at,
            indexed_at=model.indexed_at,
            chunk_count=model.chunk_count,
            embedding_model=model.embedding_model,
            error_message=model.error_message,
            metadata=model.meta_data or {},
            storage_key=getattr(model, 'storage_key', None),
            checksum=getattr(model, 'checksum', None),
            group_id=str(model.group_id) if model.group_id else None,
        )
    
    @staticmethod
    def to_model(entity: Document) -> DocumentModel:
        """Convert Domain Entity to DocumentModel"""
        status_value = entity.status.value if hasattr(entity.status, 'value') else entity.status
        return DocumentModel(
            id=uuid.UUID(entity.id) if isinstance(entity.id, str) else entity.id,
            user_id=uuid.UUID(entity.user_id) if isinstance(entity.user_id, str) else entity.user_id,
            filename=entity.filename,
            file_type=entity.file_type,
            file_size=entity.file_size,
            status=status_value,
            uploaded_at=entity.uploaded_at,
            indexed_at=entity.indexed_at,
            chunk_count=entity.chunk_count,
            embedding_model=entity.embedding_model,
            error_message=entity.error_message,
            meta_data=entity.metadata or {},
            storage_key=entity.storage_key,
            checksum=entity.checksum,
            group_id=_uuid(entity.group_id) if entity.group_id else None,
        )


class EmbeddingMapper:
    """Mapper for Embedding entity <-> EmbeddingModel"""
    
    @staticmethod
    def to_entity(model: EmbeddingModel) -> Embedding:
        """Convert EmbeddingModel to Domain Entity"""
        text = ""
        
        vector_list: List[float]
        if hasattr(model.vector, 'tolist'):
            vector_list = model.vector.tolist()
        elif isinstance(model.vector, list):
            vector_list = model.vector
        else:
            try:
                vector_list = list(model.vector)
            except (TypeError, AttributeError):
                vector_list = []
        
        return Embedding(
            id=str(model.id),
            document_id=str(model.document_id),
            chunk_id=str(model.chunk_id),
            text=text,
            vector=vector_list,
            metadata=model.meta_data or {},
            created_at=model.created_at
        )
    
    @staticmethod
    def to_model(entity: Embedding) -> EmbeddingModel:
        """Convert Domain Entity to EmbeddingModel"""
        from src.config.settings import get_settings
        settings = get_settings()
        
        return EmbeddingModel(
            id=_uuid(entity.id) or uuid.uuid4(),
            document_id=_uuid(entity.document_id),
            chunk_id=_uuid(entity.chunk_id),
            vector=entity.vector,
            model=getattr(entity, 'model', settings.hf_embedding_model),
            meta_data=entity.metadata or {},
        )


class ChunkMapper:
    """Mapper for Chunk entity <-> ChunkModel"""

    @staticmethod
    def to_entity(model: ChunkModel) -> Chunk:
        return Chunk(
            id=str(model.id),
            document_id=str(model.document_id),
            order=model.order,
            text=model.text,
            start_offset=model.start_offset,
            end_offset=model.end_offset,
            metadata=model.meta_data or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: Chunk) -> ChunkModel:
        return ChunkModel(
            id=_uuid(entity.id) or uuid.uuid4(),
            document_id=_uuid(entity.document_id),
            order=entity.order,
            text=entity.text,
            start_offset=entity.start_offset,
            end_offset=entity.end_offset,
            meta_data=entity.metadata or {},
        )


class ChatSessionMapper:
    @staticmethod
    def to_entity(model: ChatSessionModel) -> ChatSession:
        return ChatSession(
            id=str(model.id),
            user_id=str(model.user_id),
            title=model.title,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(session: ChatSession) -> ChatSessionModel:
        return ChatSessionModel(
            id=_uuid(session.id) or uuid.uuid4(),
            user_id=_uuid(session.user_id),
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )


class ChatMessageMapper:
    @staticmethod
    def to_entity(model: ChatMessageModel) -> ChatMessage:
        rag_query_id = None
        try:
            if hasattr(model, 'rag_query') and model.rag_query:
                rag_query_id = str(model.rag_query.id)
        except Exception:
            pass
        
        return ChatMessage(
            id=str(model.id),
            chat_session_id=str(model.session_id),
            role=model.role,
            content=model.content,
            metadata=model.meta_data or {},
            created_at=model.created_at,
            rag_query_id=rag_query_id,
        )

    @staticmethod
    def to_model(message: ChatMessage) -> ChatMessageModel:
        return ChatMessageModel(
            id=_uuid(message.id) or uuid.uuid4(),
            session_id=_uuid(message.chat_session_id),
            role=message.role,
            content=message.content,
            meta_data=message.metadata or {},
            created_at=message.created_at,
        )


class RagQueryMapper:
    @staticmethod
    def to_entity(model: RagQueryModel) -> RagQueryLog:
        return RagQueryLog(
            id=str(model.id),
            query_text=model.query_text,
            user_id=str(model.user_id) if model.user_id else None,
            chat_message_id=str(model.chat_message_id) if model.chat_message_id else None,
            use_multi_query=model.use_multi_query,
            use_step_back=model.use_step_back,
            top_k=model.top_k,
            status=model.status.value if isinstance(model.status, RagQueryStatus) else model.status,
            options=model.options or {},
            translated_query=model.translated_query,
            step_back_query=model.step_back_query,
            response_latency_ms=model.response_latency_ms,
            error_message=model.error_message,
            metadata=model.meta_data or {},
            created_at=model.created_at,
            completed_at=model.completed_at,
        )

    @staticmethod
    def to_model(log: RagQueryLog) -> RagQueryModel:
        try:
            status_value = RagQueryStatus(log.status)
        except ValueError:
            status_value = RagQueryStatus.COMPLETED
        return RagQueryModel(
            id=_uuid(log.id) or uuid.uuid4(),
            user_id=_uuid(log.user_id),
            chat_message_id=_uuid(log.chat_message_id),
            query_text=log.query_text,
            translated_query=log.translated_query,
            step_back_query=log.step_back_query,
            options=log.options or {},
            use_multi_query=log.use_multi_query,
            use_step_back=log.use_step_back,
            top_k=log.top_k,
            status=status_value,
            response_latency_ms=log.response_latency_ms,
            error_message=log.error_message,
            meta_data=log.metadata or {},
        )


class RagRetrievedChunkMapper:
    @staticmethod
    def from_retrieved_chunk(
        rag_query_id: str, chunk: RetrievedChunk, index: int
    ) -> RagRetrievedChunkModel:
        return RagRetrievedChunkModel(
            id=uuid.uuid4(),
            rag_query_id=_uuid(rag_query_id),
            chunk_id=_uuid(chunk.chunk_id),
            score=chunk.score,
            rank=index + 1,
            meta_data=chunk.metadata or {},
        )

    @staticmethod
    def to_entity(model: RagRetrievedChunkModel) -> RetrievedChunk:
        return RetrievedChunk(
            document_id=str(model.chunk.document_id) if model.chunk else "",
            chunk_id=str(model.chunk_id),
            content=model.chunk.text if model.chunk else "",
            score=model.score,
            metadata=model.meta_data or {},
            rank=model.rank,
        )
    
    @staticmethod
    def to_model(entity: Embedding) -> EmbeddingModel:
        """Convert Domain Entity to EmbeddingModel"""
        from pgvector.sqlalchemy import Vector
        
        return EmbeddingModel(
            id=uuid.UUID(entity.id) if isinstance(entity.id, str) else entity.id,
            document_id=uuid.UUID(entity.document_id) if isinstance(entity.document_id, str) else entity.document_id,
            chunk_id=uuid.UUID(entity.chunk_id) if isinstance(entity.chunk_id, str) else entity.chunk_id,
            text=entity.text,
            vector=entity.vector,  # Will be converted to Vector type by SQLAlchemy
            meta_data=entity.metadata,
            created_at=entity.created_at
        )


class DocumentGroupMapper:
    """Mapper for DocumentGroup entity <-> DocumentGroupModel"""
    
    @staticmethod
    def to_entity(model: DocumentGroupModel) -> DocumentGroup:
        """Convert DocumentGroupModel to Domain Entity"""
        return DocumentGroup(
            id=str(model.id),
            user_id=str(model.user_id),
            name=model.name,
            description=model.description,
            color=model.color,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
    
    @staticmethod
    def to_model(entity: DocumentGroup) -> DocumentGroupModel:
        """Convert Domain Entity to DocumentGroupModel"""
        return DocumentGroupModel(
            id=_uuid(entity.id) or uuid.uuid4(),
            user_id=_uuid(entity.user_id),
            name=entity.name,
            description=entity.description,
            color=entity.color,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class ApiTokenUsageMapper:
    @staticmethod
    def to_entity(model: ApiTokenUsageModel) -> ApiTokenUsage:
        return ApiTokenUsage(
            id=str(model.id),
            provider=model.provider,
            date=model.date,
            tokens_used=model.tokens_used,
            requests_count=model.requests_count,
            daily_limit=model.daily_limit,
            monthly_limit=model.monthly_limit,
            metadata=model.meta_data or {},
        )

    @staticmethod
    def to_model(usage: ApiTokenUsage) -> ApiTokenUsageModel:
        return ApiTokenUsageModel(
            id=_uuid(usage.id) or uuid.uuid4(),
            provider=usage.provider,
            date=usage.date,
            tokens_used=usage.tokens_used,
            requests_count=usage.requests_count,
            daily_limit=usage.daily_limit,
            monthly_limit=usage.monthly_limit,
            meta_data=usage.metadata or {},
        )

