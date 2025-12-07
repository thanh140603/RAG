"""
RAGRepositoryImpl - Infrastructure Layer
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.UserQuery import UserQuery
from src.domain.entities.RetrievedChunk import RetrievedChunk
from src.domain.repositories.RAGRepository import RAGRepository
from src.infrastructure.database.postgres.mappers import RagRetrievedChunkMapper
from src.infrastructure.database.postgres.models import (
    RagQueryModel,
    RagRetrievedChunkModel,
    RagQueryStatus,
)
from src.infrastructure.rag.retriever.retriever_service import RetrieverService
from src.infrastructure.rag.indexer.embedder import Embedder


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


class RAGRepositoryImpl(RAGRepository):
    """
    Handles retrieval pipeline + logging of rag queries
    """

    def __init__(
        self,
        retriever: RetrieverService,
        embedder: Embedder,
        db_session: AsyncSession,
    ):
        self._retriever = retriever
        self._embedder = embedder
        self._db = db_session

    async def retrieve(
        self,
        query: UserQuery,
        top_k: int = 5,
    ) -> List[RetrievedChunk]:
        """Retrieve relevant chunks for a query and log the query"""
        rag_query_model = RagQueryModel(
            id=uuid.uuid4(),
            user_id=_uuid(query.user_id),
            chat_message_id=None,
            query_text=query.query_text,
            translated_query=None,
            step_back_query=None,
            options={"query_variations": query.query_variations or []},
            use_multi_query=query.use_multi_query,
            use_step_back=query.use_step_back,
            top_k=top_k,
            status=RagQueryStatus.PENDING,
        )
        self._db.add(rag_query_model)
        await self._db.flush()

        start = time.perf_counter()
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"RAG Retrieve - Query: '{query.query_text[:100]}', User ID: {query.user_id}, Group ID: {query.group_id}, Top K: {top_k}")
            
            query_vector = await self._embedder.embed(query.query_text)
            chunks = await self._retriever.retrieve(
                query=query.query_text,
                query_vector=query_vector,
                top_k=top_k,
                user_id=query.user_id,
                group_id=query.group_id,
            )
            
            logger.info(f"RAG Retrieve - Retrieved {len(chunks)} chunks")
            if chunks:
                logger.info(f"Top chunk preview: {chunks[0].content[:200]}...")
                logger.info(f"Top chunk score: {chunks[0].score}")
            else:
                logger.warning(f"WARNING: No chunks retrieved for query: '{query.query_text}'")
                logger.warning(f"User ID: {query.user_id}, Group ID: {query.group_id}")
                logger.warning("Possible reasons:")
                logger.warning("1. No documents in the selected group")
                logger.warning("2. Documents not indexed yet")
                logger.warning("3. Query doesn't match document embeddings")

            for idx, chunk in enumerate(chunks):
                self._db.add(
                    RagRetrievedChunkMapper.from_retrieved_chunk(
                        str(rag_query_model.id), chunk, idx
                    )
                )

            rag_query_model.status = RagQueryStatus.COMPLETED
            rag_query_model.response_latency_ms = int(
                (time.perf_counter() - start) * 1000
            )
            rag_query_model.completed_at = datetime.utcnow()
            await self._db.flush()

            return chunks

        except Exception as exc:  # noqa: BLE001
            rag_query_model.status = RagQueryStatus.FAILED
            rag_query_model.error_message = str(exc)
            await self._db.flush()
            raise

    async def retrieve_multi_query(
        self,
        queries: List[str],
        top_k: int = 5,
        user_id: str | None = None,
    ) -> List[RetrievedChunk]:
        """
        Retrieve chunks for multiple query variations (no logging)
        """
        aggregated: dict[str, RetrievedChunk] = {}
        for variation in queries:
            query_vector = await self._embedder.embed(variation)
            chunks = await self._retriever.retrieve(
                query=variation,
                query_vector=query_vector,
                top_k=top_k,
                user_id=user_id,
                group_id=None,
            )
            for chunk in chunks:
                if chunk.chunk_id not in aggregated or aggregated[chunk.chunk_id].score < chunk.score:
                    aggregated[chunk.chunk_id] = chunk
        return sorted(aggregated.values(), key=lambda c: c.score, reverse=True)[:top_k]

