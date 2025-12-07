"""
DocumentRepositoryImpl - Infrastructure Layer
Single Responsibility: Implement document persistence
Liskov Substitution: Implements DocumentRepository interface
"""
from __future__ import annotations

from typing import List, Optional
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.Document import Document, DocumentStatus
from src.domain.repositories.DocumentRepository import DocumentRepository
from src.infrastructure.database.postgres.mappers import DocumentMapper
from src.infrastructure.database.postgres.models import DocumentModel


def _to_uuid(value: str | uuid.UUID | None) -> uuid.UUID | None:
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


class DocumentRepositoryImpl(DocumentRepository):
    """
    Document Repository Implementation
    Single Responsibility: Handle database operations for documents
    """

    def __init__(self, db_session: AsyncSession):
        self._db = db_session

    async def create(self, document: Document) -> Document:
        """Create a new document"""
        model = DocumentMapper.to_model(document)
        self._db.add(model)
        await self._db.flush()
        await self._db.refresh(model)
        return DocumentMapper.to_entity(model)

    async def get_by_id(self, document_id: str) -> Optional[Document]:
        """Get document by ID"""
        model = await self._get_model(document_id)
        return DocumentMapper.to_entity(model) if model else None

    async def get_by_user_id(self, user_id: str) -> List[Document]:
        """Get all documents for a user"""
        user_uuid = _to_uuid(user_id)
        if user_uuid is None:
            return []
        stmt = (
            select(DocumentModel)
            .where(DocumentModel.user_id == user_uuid)
            .order_by(DocumentModel.uploaded_at.desc())
        )
        result = await self._db.execute(stmt)
        models = result.scalars().all()
        return [DocumentMapper.to_entity(model) for model in models]

    async def update_status(
        self,
        document_id: str,
        status: DocumentStatus,
        **kwargs,
    ) -> Document:
        """Update document status and optional fields"""
        model = await self._get_model(document_id)
        if not model:
            raise ValueError(f"Document {document_id} not found")

        model.status = status

        allowed_fields = {
            "chunk_count",
            "embedding_model",
            "error_message",
            "indexed_at",
        }
        for key, value in kwargs.items():
            if key in allowed_fields and hasattr(model, key):
                setattr(model, key, value)

        await self._db.flush()
        await self._db.refresh(model)
        return DocumentMapper.to_entity(model)

    async def delete(self, document_id: str) -> bool:
        """Delete a document"""
        model = await self._get_model(document_id)
        if not model:
            return False

        await self._db.delete(model)
        await self._db.flush()
        return True

    async def exists(self, document_id: str) -> bool:
        """Check if document exists"""
        doc_uuid = _to_uuid(document_id)
        if doc_uuid is None:
            return False
        stmt = (
            select(func.count())
            .select_from(DocumentModel)
            .where(DocumentModel.id == doc_uuid)
        )
        result = await self._db.execute(stmt)
        return result.scalar_one() > 0

    async def _get_model(self, document_id: str) -> Optional[DocumentModel]:
        doc_uuid = _to_uuid(document_id)
        if doc_uuid is None:
            return None
        stmt = select(DocumentModel).where(
            DocumentModel.id == doc_uuid
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_file_info(
        self,
        document_id: str,
        *,
        file_size: int | None = None,
        metadata: Optional[dict] = None,
        group_id: Optional[str] = None,
    ) -> Document:
        """Update file size, metadata, or group_id for a document."""
        model = await self._get_model(document_id)
        if not model:
            raise ValueError(f"Document {document_id} not found")

        if file_size is not None:
            model.file_size = file_size

        if metadata:
            merged = dict(model.meta_data or {})
            merged.update(metadata)
            model.meta_data = merged

        if group_id is not None:
            model.group_id = _to_uuid(group_id) if group_id else None

        await self._db.flush()
        await self._db.refresh(model)
        return DocumentMapper.to_entity(model)

