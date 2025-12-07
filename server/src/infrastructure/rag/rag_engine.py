"""
RAGEngine - Infrastructure Layer
Single Responsibility: Orchestrate complete RAG pipeline
"""
from typing import List
from src.domain.entities.UserQuery import UserQuery
from src.domain.entities.RetrievedChunk import RetrievedChunk
from src.infrastructure.rag.indexer.indexer_service import IndexerService
from src.infrastructure.rag.retriever.retriever_service import RetrieverService
from src.infrastructure.rag.query_transformation.multi_query import MultiQueryGenerator
from src.infrastructure.rag.query_transformation.step_back_prompt import StepBackPromptGenerator
from src.infrastructure.rag.reranker.rrf_fusion import RRFFusion
from src.infrastructure.rag.generator.llm_generator import LLMGenerator


class RAGEngine:
    """
    Main RAG engine
    Single Responsibility: Coordinate RAG pipeline components
    """
    
    def __init__(
        self,
        indexer: IndexerService,
        retriever: RetrieverService,
        multi_query_generator: MultiQueryGenerator,
        step_back_generator: StepBackPromptGenerator,
        reranker: RRFFusion,
        generator: LLMGenerator
    ):
        self._indexer = indexer
        self._retriever = retriever
        self._multi_query_generator = multi_query_generator
        self._step_back_generator = step_back_generator
        self._reranker = reranker
        self._generator = generator
    
    async def index_document(self, chunks, embeddings) -> None:
        """Index a document"""
        await self._indexer.index(chunks, embeddings)
    
    async def query(self, query: UserQuery, top_k: int = 5) -> dict:
        """Execute RAG query"""
        # TODO: Implement full RAG pipeline
        # This orchestrates all components
        return {}

