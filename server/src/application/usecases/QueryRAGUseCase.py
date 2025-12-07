"""
QueryRAGUseCase - Application Layer
Single Responsibility: Orchestrate RAG query workflow
"""
from __future__ import annotations

import logging
from typing import List

from src.config.settings import get_settings
from src.domain.entities.RetrievedChunk import RetrievedChunk
from src.domain.entities.UserQuery import UserQuery
from src.domain.repositories.RAGRepository import RAGRepository
from src.infrastructure.rag.external.web_search_service import WebSearchService
from src.infrastructure.rag.generator.llm_generator import LLMGenerator
from src.infrastructure.rag.query_transformation.multi_query import MultiQueryGenerator
from src.infrastructure.rag.query_transformation.step_back_prompt import StepBackPromptGenerator
from src.infrastructure.rag.reranker.rrf_fusion import RRFFusion

settings = get_settings()
logger = logging.getLogger(__name__)


class QueryRAGUseCase:
    """
    Use Case: Query RAG system
    Single Responsibility: Handle RAG query business logic
    """
    
    def __init__(
        self,
        rag_repository: RAGRepository,
        multi_query_generator: MultiQueryGenerator,
        step_back_generator: StepBackPromptGenerator,
        reranker: RRFFusion,
        llm_generator: LLMGenerator,
        web_search_service: WebSearchService | None = None,
    ):
        self._rag_repository = rag_repository
        self._multi_query_generator = multi_query_generator
        self._step_back_generator = step_back_generator
        self._reranker = reranker
        self._llm_generator = llm_generator
        self._web_search_service = web_search_service
    
    async def execute(
        self,
        query: UserQuery,
        top_k: int = 10,
        conversation_history: List = None,
    ) -> dict:
        """
        Execute RAG query workflow:
        1. Query Translation (multi-query)
        2. Step-back prompting (optional)
        3. Retrieval (for each query)
        4. RAG Fusion (merge + rank)
        5. Generation (LLM synthesis)
        """
        logger.info(
            "Executing RAG query user=%s chat=%s multi_query=%s step_back=%s",
            query.user_id,
            query.chat_id,
            query.use_multi_query and settings.use_multi_query,
            query.use_step_back and settings.use_step_back_prompting,
        )

        queries_to_retrieve: List[str] = [query.query_text]
        generated_variations: List[str] = []
        step_back_query: str | None = None

        if query.use_multi_query and settings.use_multi_query:
            generated_variations = await self._multi_query_generator.generate(
                query.query_text
            )
            for variation in generated_variations:
                if variation and variation not in queries_to_retrieve:
                    queries_to_retrieve.append(variation)
            logger.debug(
                "Generated %d query variations for user=%s",
                len(generated_variations),
                query.user_id,
            )

        if query.use_step_back and settings.use_step_back_prompting:
            step_back_query = await self._step_back_generator.generate(
                query.query_text
            )
            if step_back_query and step_back_query not in queries_to_retrieve:
                queries_to_retrieve.append(step_back_query)
            logger.debug("Generated step-back query for user=%s", query.user_id)

        query.query_variations = generated_variations

        primary_chunks = await self._rag_repository.retrieve(query, top_k)
        result_sets: List[List[RetrievedChunk]] = []
        if primary_chunks:
            result_sets.append(primary_chunks)

        variation_queries = [
            q for q in queries_to_retrieve if q != query.query_text
        ]
        variation_chunks: List[RetrievedChunk] = []
        if variation_queries:
            variation_chunks = await self._rag_repository.retrieve_multi_query(
                variation_queries,
                top_k,
            )
            if variation_chunks:
                result_sets.append(variation_chunks)

        fused_chunks: List[RetrievedChunk] = []
        if result_sets:
            if settings.use_reranking and len(result_sets) > 1:
                fused_chunks = await self._reranker.fuse(result_sets, top_k)
            else:
                seen: set[tuple[str, str]] = set()
                ordered: List[RetrievedChunk] = []
                for chunk_list in result_sets:
                    for chunk in chunk_list:
                        key = (chunk.document_id, chunk.chunk_id)
                        if key in seen:
                            continue
                        seen.add(key)
                        ordered.append(chunk)
                fused_chunks = ordered[:top_k]

        internal_context_parts = []
        for chunk in fused_chunks:
            if chunk.content and chunk.content.strip():
                internal_context_parts.append(chunk.content.strip())
        
        internal_context = "\n\n".join(internal_context_parts) if internal_context_parts else ""
        
        logger.info(f"Formatted internal context with {len(fused_chunks)} chunks, {len(internal_context_parts)} non-empty chunks, total length: {len(internal_context)}")
        if fused_chunks:
            logger.info(f"Top chunk (rank 1) preview: {fused_chunks[0].content[:200]}...")
            if hasattr(fused_chunks[0], 'similarity_score'):
                logger.info(f"Top chunk similarity score: {fused_chunks[0].similarity_score}")
        else:
            logger.warning(f"WARNING: No chunks retrieved for query: {query.query_text}")
            logger.warning(f"Query: {query.query_text}")
            logger.warning(f"Group ID: {query.group_id}")
            logger.warning("This could mean:")
            logger.warning("1. No documents in the selected group")
            logger.warning("2. Documents not indexed yet")
            logger.warning("3. Query doesn't match document content semantically")
        
        external_context = ""
        should_use_web_search = False
        
        if self._web_search_service is not None and settings.enable_web_search:
            if len(fused_chunks) == 0:
                should_use_web_search = True
                logger.info(f"No internal chunks found, triggering web search for query: {query.query_text[:50]}")
            else:
                logger.info(f"Found {len(fused_chunks)} internal chunks, skipping web search to prioritize internal documents")
                should_use_web_search = False
        
        if should_use_web_search:
            logger.info(f"Triggering web search for query: {query.query_text[:50]}")
            web_results = await self._web_search_service.search(query.query_text, token_tracker=self._token_tracker)
            if web_results:
                external_context = self._web_search_service.format_results_as_context(web_results)
                logger.info(f"Web search returned {len(web_results)} results")
        
        answer = await self._llm_generator.generate(
            query.query_text,
            internal_context,
            external_context=external_context,
            conversation_history=conversation_history or [],
        )

        logger.info(
            "RAG query complete user=%s chunks=%d variations=%d",
            query.user_id,
            len(fused_chunks),
            len(generated_variations),
        )

        return {
            "answer": answer,
            "retrieved_chunks": fused_chunks,
            "query_variations": generated_variations,
            "step_back_query": step_back_query,
        }

