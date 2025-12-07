"""
Database Models - SQLAlchemy
Single Responsibility: Define database schema
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from src.domain.entities.Document import DocumentStatus
from src.infrastructure.database.postgres.base import Base


class RagQueryStatus(PyEnum):
    """RAG query status enum"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentGroupModel(Base):
    """
    DocumentGroup database model
    Maps to domain entity: DocumentGroup
    """
    __tablename__ = "document_groups"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    color: Mapped[Optional[str]] = mapped_column(String(7))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="document_groups")
    documents: Mapped[List["DocumentModel"]] = relationship(
        "DocumentModel",
        back_populates="group",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<DocumentGroupModel(id={self.id}, name={self.name})>"


class DocumentModel(Base):
    """
    Document database model
    Maps to domain entity: Document
    """
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("document_groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=DocumentStatus.PENDING,
        index=True,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    indexed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    chunk_count: Mapped[Optional[int]] = mapped_column(Integer)
    embedding_model: Mapped[Optional[str]] = mapped_column(String(100))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    storage_key: Mapped[Optional[str]] = mapped_column(String(500))
    checksum: Mapped[Optional[str]] = mapped_column(String(64))
    meta_data: Mapped[dict] = mapped_column(JSONB, name="metadata", nullable=True, default=dict)

    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="documents")
    group: Mapped[Optional["DocumentGroupModel"]] = relationship(
        "DocumentGroupModel", back_populates="documents"
    )
    chunks: Mapped[List["ChunkModel"]] = relationship(
        "ChunkModel",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="ChunkModel.order",
    )
    embeddings: Mapped[List["EmbeddingModel"]] = relationship(
        "EmbeddingModel",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<DocumentModel(id={self.id}, filename={self.filename}, status={self.status})>"


class ChunkModel(Base):
    """
    Chunk database model
    Represents a chunk of a document
    """
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    start_offset: Mapped[Optional[int]] = mapped_column(Integer)
    end_offset: Mapped[Optional[int]] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    meta_data: Mapped[dict] = mapped_column(JSONB, name="metadata", nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    document: Mapped["DocumentModel"] = relationship("DocumentModel", back_populates="chunks")
    embeddings: Mapped[List["EmbeddingModel"]] = relationship(
        "EmbeddingModel",
        back_populates="chunk",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("document_id", "order", name="uq_chunk_document_order"),
    )

    def __repr__(self):
        return f"<ChunkModel(id={self.id}, document_id={self.document_id}, order={self.order})>"


class EmbeddingModel(Base):
    """
    Embedding database model
    Stores vector embeddings for chunks
    """
    __tablename__ = "embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chunks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vector: Mapped[List[float]] = mapped_column(Vector(1536), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    meta_data: Mapped[dict] = mapped_column(JSONB, name="metadata", nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    chunk: Mapped["ChunkModel"] = relationship("ChunkModel", back_populates="embeddings")
    document: Mapped["DocumentModel"] = relationship("DocumentModel", back_populates="embeddings")

    __table_args__ = (
        Index("ix_embeddings_vector", "vector", postgresql_using="ivfflat"),
    )

    def __repr__(self):
        return f"<EmbeddingModel(id={self.id}, chunk_id={self.chunk_id}, model={self.model})>"


class UserModel(Base):
    """
    User database model
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), nullable=False, server_default="user", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    documents: Mapped[List["DocumentModel"]] = relationship(
        "DocumentModel", back_populates="user", cascade="all, delete-orphan"
    )
    document_groups: Mapped[List["DocumentGroupModel"]] = relationship(
        "DocumentGroupModel", back_populates="user", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[List["ChatSessionModel"]] = relationship(
        "ChatSessionModel", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<UserModel(id={self.id}, email={self.email})>"


class ChatSessionModel(Base):
    """
    Chat session database model
    """
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="chat_sessions")
    messages: Mapped[List["ChatMessageModel"]] = relationship(
        "ChatMessageModel", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ChatSessionModel(id={self.id}, user_id={self.user_id})>"


class ChatMessageModel(Base):
    """
    Chat message database model
    """
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        name="chat_session_id",
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta_data: Mapped[dict] = mapped_column(JSONB, name="metadata", nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped["ChatSessionModel"] = relationship("ChatSessionModel", back_populates="messages")
    rag_query: Mapped[Optional["RagQueryModel"]] = relationship(
        "RagQueryModel", 
        foreign_keys="[RagQueryModel.chat_message_id]",
        uselist=False,
        back_populates=None,  # RagQueryModel doesn't have back_populates for chat_message
    )

    def __repr__(self):
        return f"<ChatMessageModel(id={self.id}, session_id={self.session_id}, role={self.role})>"


class RagQueryModel(Base):
    """
    RAG query log database model
    """
    __tablename__ = "rag_queries"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    chat_message_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chat_messages.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        index=True,
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    translated_query: Mapped[Optional[str]] = mapped_column(Text)
    step_back_query: Mapped[Optional[str]] = mapped_column(Text)
    options: Mapped[Optional[dict]] = mapped_column(JSONB)
    use_multi_query: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    use_step_back: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    top_k: Mapped[int] = mapped_column(Integer, nullable=False, server_default="5")
    status: Mapped[RagQueryStatus] = mapped_column(
        Enum(RagQueryStatus, name="rag_query_status", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=RagQueryStatus.PENDING,
    )
    response_latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    meta_data: Mapped[dict] = mapped_column(JSONB, name="metadata", nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    retrieved_chunks: Mapped[List["RagRetrievedChunkModel"]] = relationship(
        "RagRetrievedChunkModel", back_populates="rag_query", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<RagQueryModel(id={self.id}, status={self.status})>"


class RagRetrievedChunkModel(Base):
    """
    RAG retrieved chunk database model
    Links retrieved chunks to RAG queries
    """
    __tablename__ = "rag_retrieved_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rag_query_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("rag_queries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chunks.id", ondelete="CASCADE"),
        nullable=False,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    meta_data: Mapped[dict] = mapped_column(JSONB, name="metadata", nullable=True, default=dict)

    # Relationships
    rag_query: Mapped["RagQueryModel"] = relationship("RagQueryModel", back_populates="retrieved_chunks")

    def __repr__(self):
        return f"<RagRetrievedChunkModel(id={self.id}, rag_query_id={self.rag_query_id}, score={self.score})>"


class ApiTokenUsageModel(Base):
    """
    API Token Usage tracking database model
    Tracks token usage for external APIs (Groq, Tavily, etc.)
    """
    __tablename__ = "api_token_usage"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # 'groq', 'tavily', etc.
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True, server_default=func.now()
    )
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    requests_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    daily_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    monthly_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    meta_data: Mapped[dict] = mapped_column(JSONB, name="metadata", nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint('provider', 'date', name='uq_api_token_usage_provider_date'),
        Index('ix_api_token_usage_provider_date', 'provider', 'date'),
    )

    def __repr__(self):
        return f"<ApiTokenUsageModel(id={self.id}, provider={self.provider}, date={self.date.date()}, tokens_used={self.tokens_used})>"
