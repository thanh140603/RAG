"""
OpenAIClient - Infrastructure Layer

Chat: Groq (OpenAI-compatible API)
Embeddings: local sentence-transformers (no external HTTP calls).
"""
from __future__ import annotations

import asyncio
from typing import List

from openai import OpenAI
from sentence_transformers import SentenceTransformer

from src.config.settings import get_settings

settings = get_settings()


class OpenAIClient:
    """
    Generic LLM client using OpenAI-compatible APIs (Groq by default) for chat,
    with local sentence-transformers used for embeddings.
    """

    def __init__(self) -> None:
        """
        Initialize underlying client.

        - Groq (via base_url override) for chat completions.
        - Local sentence-transformers model for embeddings.
        """
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is not configured")

        self._client = OpenAI(
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
        )
        self._model = settings.groq_model

        local_model_name = getattr(settings, "hf_embedding_model", None) or "sentence-transformers/all-MiniLM-L6-v2"
        self._st_model = SentenceTransformer(local_model_name)
        self._target_dim = getattr(settings, "embedding_dimension", 1536)

    async def create_embedding(self, text: str) -> List[float]:
        """
        Tạo embedding bằng model local sentence-transformers.
        Vector sẽ được pad/trim về đúng kích thước embedding_dimension (mặc định 1536)
        để khớp với schema cột Vector(1536) trong PostgreSQL.
        """

        def _local() -> List[float]:
            vec = self._st_model.encode(text)
            if not isinstance(vec, list):
                vec = vec.tolist()

            d = len(vec)
            if d > self._target_dim:
                vec = vec[: self._target_dim]
            elif d < self._target_dim:
                vec = vec + [0.0] * (self._target_dim - d)
            return vec

        return await asyncio.to_thread(_local)

    async def chat_completion(
        self,
        messages: List[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
        token_tracker=None,
    ) -> str:
        """
        Generate chat completion using Groq (OpenAI-compatible API).
        """

        def _call() -> tuple[str, int]:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content or ""
            usage = response.usage
            tokens_used = (usage.total_tokens if usage else 0) if hasattr(response, 'usage') and response.usage else 0
            return content, tokens_used

        content, tokens_used = await asyncio.to_thread(_call)
        
        if token_tracker and tokens_used > 0:
            await token_tracker.track_usage_async("groq", tokens_used, requests_count=1)
        
        return content


