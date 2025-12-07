"""
PgVectorStore - Infrastructure Layer
Single Responsibility: Interface with pgvector database
"""
from typing import List, Optional, Tuple
import uuid
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.Embedding import Embedding
from src.infrastructure.database.postgres.mappers import EmbeddingMapper
from src.infrastructure.database.postgres.models import EmbeddingModel, DocumentModel, ChunkModel

logger = logging.getLogger(__name__)


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


class PgVectorStore:
    """
    PostgreSQL + pgvector store
    Single Responsibility: Handle pgvector operations
    """
    
    def __init__(self, db_session: AsyncSession):
        self._db = db_session
    
    async def add_embeddings(self, embeddings: List[Embedding]) -> bool:
        """Add embeddings to vector store"""
        try:
            models = [EmbeddingMapper.to_model(embedding) for embedding in embeddings]
            self._db.add_all(models)
            await self._db.flush()
            for model in models:
                await self._db.refresh(model)
            return True
        except Exception as e:
            logger.error(f"Failed to add embeddings: {e}")
            return False
    
    async def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_metadata: Optional[dict] = None,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
    ) -> List[Tuple[Embedding, float]]:
        """
        Search for similar vectors using pgvector cosine distance
        
        Args:
            query_vector: Query vector to search for
            top_k: Number of results to return
            filter_metadata: Optional metadata filter
            user_id: Optional user ID filter
            group_id: Optional group ID filter
            
        Returns:
            List of tuples (Embedding, score) sorted by similarity
        """
        logger.info(f"PgVectorStore.search - Top K: {top_k}, User ID: {user_id}, Group ID: {group_id}")
        
        distance = EmbeddingModel.vector.cosine_distance(query_vector).label("distance")
        stmt = (
            select(EmbeddingModel, ChunkModel.text, distance)
            .join(ChunkModel, EmbeddingModel.chunk_id == ChunkModel.id)
            .order_by(distance)
        )

        needs_doc_join = user_id is not None or group_id is not None
        if needs_doc_join:
            stmt = stmt.join(
                DocumentModel, EmbeddingModel.document_id == DocumentModel.id
            )
        
        if user_id is not None:
            user_uuid = _to_uuid(user_id)
            if user_uuid is not None:
                stmt = stmt.where(DocumentModel.user_id == user_uuid)
                logger.info(f"Filtering by user_id: {user_uuid}")
            else:
                logger.warning(f"Invalid user_id format: {user_id}")

        if group_id is not None:
            group_uuid = _to_uuid(group_id)
            if group_uuid is not None:
                stmt = stmt.where(DocumentModel.group_id == group_uuid)
                logger.info(f"Filtering by group_id: {group_uuid}")
            else:
                logger.warning(f"Invalid group_id format: {group_id}")
        else:
            logger.info("No group_id filter - searching all groups")

        if filter_metadata:
            stmt = stmt.where(EmbeddingModel.meta_data.contains(filter_metadata))
        stmt = stmt.limit(top_k)

        result = await self._db.execute(stmt)
        rows = result.all()
        
        logger.info(f"PgVectorStore.search - Found {len(rows)} matches")
        if rows:
            top_score = 1 - rows[0][2] if rows[0][2] is not None else 0.0
            logger.info(f"Top match score: {top_score:.4f}")
            logger.info(f"Top match text preview: {rows[0][1][:100] if rows[0][1] else 'EMPTY'}...")
        else:
            logger.warning("No embeddings found matching the query!")
            logger.warning(f"Query vector dimension: {len(query_vector)}")
            logger.warning(f"Filters: user_id={user_id}, group_id={group_id}")
        
        matches = []
        for model, chunk_text, dist in rows:
            score = 1 - dist if dist is not None else 0.0
            embedding_entity = EmbeddingMapper.to_entity(model)
            embedding_entity.text = chunk_text or ""
            matches.append((embedding_entity, score))
        return matches
