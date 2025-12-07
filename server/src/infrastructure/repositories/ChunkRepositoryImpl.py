"""
ChunkRepositoryImpl - Infrastructure Layer
"""
from __future__ import annotations

import re
import math
from typing import List, Tuple
from collections import Counter
import uuid

from sqlalchemy import delete, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.Chunk import Chunk
from src.domain.repositories.ChunkRepository import ChunkRepository
from src.infrastructure.database.postgres.mappers import ChunkMapper
from src.infrastructure.database.postgres.models import ChunkModel, DocumentModel


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


class ChunkRepositoryImpl(ChunkRepository):
    def __init__(self, db_session: AsyncSession):
        self._db = db_session

    async def create_many(self, chunks: List[Chunk]) -> List[Chunk]:
        models = [ChunkMapper.to_model(chunk) for chunk in chunks]
        self._db.add_all(models)
        await self._db.flush()
        for model in models:
            await self._db.refresh(model)
        return [ChunkMapper.to_entity(model) for model in models]

    async def get_by_document_id(self, document_id: str) -> List[Chunk]:
        doc_uuid = _uuid(document_id)
        if doc_uuid is None:
            return []
        stmt = (
            select(ChunkModel)
            .where(ChunkModel.document_id == doc_uuid)
            .order_by(ChunkModel.order.asc())
        )
        result = await self._db.execute(stmt)
        models = result.scalars().all()
        return [ChunkMapper.to_entity(model) for model in models]

    async def delete_by_document_id(self, document_id: str) -> None:
        doc_uuid = _uuid(document_id)
        if doc_uuid is None:
            return
        stmt = delete(ChunkModel).where(
            ChunkModel.document_id == doc_uuid
        )
        await self._db.execute(stmt)
        await self._db.flush()

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words (lowercase, alphanumeric only)"""
        tokens = re.findall(r"\b\w+\b", text.lower())
        return tokens

    async def search_bm25(
        self,
        query: str,
        top_k: int = 5,
        user_id: str | None = None,
        group_id: str | None = None,
    ) -> List[Tuple[Chunk, float]]:
        """
        Search chunks using BM25 algorithm
        Returns list of (chunk, bm25_score) tuples sorted by score descending
        """
        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        # Get all chunks (optionally scoped to a user's documents and/or group)
        # For BM25, we need all candidate chunks to calculate document frequencies
        stmt = select(ChunkModel)
        needs_join = user_id is not None or group_id is not None
        if needs_join:
            stmt = stmt.join(
                DocumentModel, ChunkModel.document_id == DocumentModel.id
            )
        
        if user_id is not None:
            user_uuid = _uuid(user_id)
            if user_uuid is not None:
                stmt = stmt.where(DocumentModel.user_id == user_uuid)
        
        if group_id is not None:
            group_uuid = _uuid(group_id)
            if group_uuid is not None:
                stmt = stmt.where(DocumentModel.group_id == group_uuid)
        
        result = await self._db.execute(stmt)
        all_chunks = result.scalars().all()
        
        if not all_chunks:
            return []

        # Convert to entities
        chunks = [ChunkMapper.to_entity(model) for model in all_chunks]

        # Build term frequency index
        doc_lengths: dict[str, int] = {}
        term_freqs: dict[str, dict[str, int]] = {}  # chunk_id -> {term: count}
        doc_freqs: dict[str, set[str]] = {}  # term -> set of chunk_ids

        for chunk in chunks:
            tokens = self._tokenize(chunk.text)
            doc_lengths[str(chunk.id)] = len(tokens)
            
            # Count term frequencies in this document
            term_counts = Counter(tokens)
            term_freqs[str(chunk.id)] = dict(term_counts)
            
            # Track which documents contain each term
            for term in term_counts.keys():
                if term not in doc_freqs:
                    doc_freqs[term] = set()
                doc_freqs[term].add(str(chunk.id))

        # Calculate average document length
        total_length = sum(doc_lengths.values())
        avg_doc_length = total_length / len(chunks) if chunks else 1.0

        # BM25 parameters
        k1 = 1.5
        b = 0.75

        # Calculate BM25 scores
        scores: list[Tuple[Chunk, float]] = []
        total_docs = len(chunks)

        for chunk in chunks:
            chunk_id = str(chunk.id)
            doc_length = doc_lengths.get(chunk_id, 1)
            score = 0.0

            for term in query_terms:
                # IDF (Inverse Document Frequency)
                df = len(doc_freqs.get(term, set()))
                if df == 0:
                    continue
                
                # Standard BM25 IDF formula
                idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1.0)

                # Term frequency in this document
                tf = term_freqs.get(chunk_id, {}).get(term, 0)
                if tf == 0:
                    continue

                # BM25 term score
                # score = IDF * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_length / avg_doc_length)))
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * (doc_length / avg_doc_length))
                term_score = idf * (numerator / denominator)
                score += term_score

            if score > 0:
                scores.append((chunk, score))

        # Sort by score descending and return top_k
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

