"""
MultiQueryGenerator - Infrastructure Layer
Single Responsibility: Generate multiple query variations
"""
import re
from typing import List
from src.infrastructure.llm.openai_client import OpenAIClient
from src.config.settings import get_settings

settings = get_settings()


class MultiQueryGenerator:
    """
    Multi-query generator
    Single Responsibility: Generate query variations for better retrieval
    """
    
    def __init__(self, llm_client: OpenAIClient):
        self._llm_client = llm_client
        self._count = settings.multi_query_count
    
    async def generate(self, query: str) -> List[str]:
        """
        Generate multiple query variations
        """
        if not query:
            return []

        system_prompt = (
            "You rewrite user questions into alternative phrasings that preserve intent. "
            "Return each variation on its own line with no numbering."
        )
        user_prompt = (
            f"Original question: {query}\n"
            f"Provide {self._count} diverse retrieval-friendly variations."
        )

        response = await self._llm_client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )

        candidates: List[str] = []
        for line in response.splitlines():
            cleaned = re.sub(r"^\s*[-\d\.)]+\s*", "", line).strip()
            if cleaned:
                candidates.append(cleaned)

        unique: List[str] = []
        seen = set()
        for variant in candidates:
            normalized = variant.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            unique.append(variant)
            if len(unique) >= self._count:
                break

        if not unique:
            unique.append(query)

        return unique

