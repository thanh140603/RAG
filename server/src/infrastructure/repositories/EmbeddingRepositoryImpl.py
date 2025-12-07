"""
EmbeddingRepositoryImpl - Infrastructure Layer
Single Responsibility: Implement embedding persistence
"""
from __future__ import annotations

from typing import List, Optional, Tuple
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.Embedding import Embedding
from src.domain.repositories.EmbeddingRepository import EmbeddingRepository
from src.infrastructure.database.postgres.mappers import EmbeddingMapper
from src.infrastructure.database.postgres.models import EmbeddingModel
from src.infrastructure.vector_store.pgvector.pgvector_store import PgVectorStore


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


class EmbeddingRepositoryImpl(EmbeddingRepository):
    """
    Embedding Repository Implementation
    Single Responsibility: Handle vector store operations
    """

    def __init__(self, db_session: AsyncSession):
        self._db = db_session
        self._vector_store = PgVectorStore(db_session)

    async def create(self, embedding: Embedding) -> Embedding:
        """Create a new embedding"""
        model = EmbeddingMapper.to_model(embedding)
        self._db.add(model)
        await self._db.flush()
        await self._db.refresh(model)
        return EmbeddingMapper.to_entity(model)

    async def create_batch(self, embeddings: List[Embedding]) -> List[Embedding]:
        """Create multiple embeddings"""
        models = [EmbeddingMapper.to_model(embedding) for embedding in embeddings]
        self._db.add_all(models)
        await self._db.flush()
        for model in models:
            await self._db.refresh(model)
        
        entities = []
        for model in models:
            vector_data = model.vector
            entity = Embedding(
                id=str(model.id),
                document_id=str(model.document_id),
                chunk_id=str(model.chunk_id),
                text="",
                vector=vector_data.tolist() if hasattr(vector_data, 'tolist') else list(vector_data) if vector_data else [],
                metadata=model.meta_data or {},
                created_at=model.created_at
            )
            entities.append(entity)
        return entities

    async def get_by_document_id(self, document_id: str) -> List[Embedding]:
        """Get all embeddings for a document"""
        doc_uuid = _to_uuid(document_id)
        if doc_uuid is None:
            return []
        stmt = select(EmbeddingModel).where(
            EmbeddingModel.document_id == doc_uuid
        )
        result = await self._db.execute(stmt)
        models = result.scalars().all()
        return [EmbeddingMapper.to_entity(model) for model in models]

    async def delete_by_document_id(self, document_id: str) -> bool:
        """Delete all embeddings for a document"""
        doc_uuid = _to_uuid(document_id)
        if doc_uuid is None:
            return False
        stmt = delete(EmbeddingModel).where(
            EmbeddingModel.document_id == doc_uuid
        )
        result = await self._db.execute(stmt)
        await self._db.flush()
        return (result.rowcount or 0) > 0

    async def search_similar(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_metadata: Optional[dict] = None,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
    ) -> List[tuple[Embedding, float]]:
        """Search for similar embeddings using pgvector distance"""
        return await self._vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            filter_metadata=filter_metadata,
            user_id=user_id,
            group_id=group_id,
        )

