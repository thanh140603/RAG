"""
Embedder - Infrastructure Layer
"""
from __future__ import annotations

from typing import List

from src.infrastructure.llm.openai_client import OpenAIClient
from src.config.settings import get_settings

settings = get_settings()


class Embedder:
    """
    Text embedder responsible for generating vector representations
    """

    def __init__(self, openai_client: OpenAIClient):
        if openai_client is None:
            raise ValueError("OpenAI client is required for embedding generation")
        self._openai_client = openai_client

    async def embed(self, text: str) -> List[float]:
        if not text:
            return []
        return await self._openai_client.create_embedding(text)

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        vectors: List[List[float]] = []
        for text in texts:
            vectors.append(await self.embed(text))
        return vectors

