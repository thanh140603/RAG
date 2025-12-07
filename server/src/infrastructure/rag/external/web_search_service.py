"""
WebSearchService - Infrastructure Layer
Single Responsibility: Search external knowledge sources (web) for additional context
"""
from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

import httpx

from src.config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class WebSearchResult:
    """Represents a single web search result"""
    def __init__(self, title: str, url: str, content: str, score: float = 1.0):
        self.title = title
        self.url = url
        self.content = content
        self.score = score


class WebSearchService:
    """
    Service for searching external knowledge sources (web search)
    
    Supports multiple providers:
    - Tavily API (recommended, has free tier)
    - Serper API (alternative)
    - Custom web search APIs
    """

    def __init__(self, token_tracker=None):
        self._tavily_api_key: Optional[str] = settings.tavily_api_key
        self._serper_api_key: Optional[str] = settings.serper_api_key
        self._web_search_enabled: bool = settings.enable_web_search
        self._web_search_provider: str = settings.web_search_provider
        self._max_results: int = settings.web_search_max_results
        self._token_tracker = token_tracker  # Optional TokenTracker for tracking usage

    async def search(self, query: str, max_results: Optional[int] = None) -> List[WebSearchResult]:
        """
        Search the web for additional context
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of WebSearchResult objects
        """
        if not self._web_search_enabled:
            logger.debug("Web search is disabled")
            return []

        max_results = max_results or self._max_results

        if self._web_search_provider == "tavily" and self._tavily_api_key:
            return await self._search_tavily(query, max_results)
        elif self._web_search_provider == "serper" and self._serper_api_key:
            return await self._search_serper(query, max_results)
        else:
            logger.warning(f"Web search provider '{self._web_search_provider}' not configured or not available")
            return []

    async def _search_tavily(self, query: str, max_results: int) -> List[WebSearchResult]:
        """
        Search using Tavily API
        Docs: https://docs.tavily.com/
        """
        if not self._tavily_api_key:
            logger.warning("Tavily API key not configured")
            return []

        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self._tavily_api_key,
            "query": query,
            "max_results": max_results,
            "include_answer": True,
            "include_raw_content": False,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

                results = []
                
                # Tavily returns an "answer" field with a summary
                if "answer" in data and data["answer"]:
                    results.append(WebSearchResult(
                        title="Tavily Summary",
                        url="",
                        content=data["answer"],
                        score=1.0,
                    ))

                # Tavily also returns individual results
                for item in data.get("results", [])[:max_results]:
                    results.append(WebSearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        content=item.get("content", ""),
                        score=item.get("score", 1.0),
                    ))

                logger.info(f"Tavily search returned {len(results)} results for query: {query[:50]}")
                
                # Track token usage (Tavily charges per request, estimate 1 token per request)
                # In reality, Tavily doesn't use tokens, but we track requests
                if hasattr(self, '_token_tracker') and self._token_tracker:
                    await self._token_tracker.track_usage_async("tavily", tokens_used=1, requests_count=1)
                
                return results

        except Exception as e:
            logger.error(f"Tavily search failed: {e}", exc_info=True)
            return []

    async def _search_serper(self, query: str, max_results: int) -> List[WebSearchResult]:
        """
        Search using Serper API
        Docs: https://serper.dev/
        """
        if not self._serper_api_key:
            logger.warning("Serper API key not configured")
            return []

        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": self._serper_api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "q": query,
            "num": max_results,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()

                results = []
                
                # Serper returns organic results
                for item in data.get("organic", [])[:max_results]:
                    results.append(WebSearchResult(
                        title=item.get("title", ""),
                        url=item.get("link", ""),
                        content=item.get("snippet", ""),
                        score=1.0,
                    ))

                # Serper also returns answer box if available
                if "answerBox" in data:
                    answer_box = data["answerBox"]
                    results.insert(0, WebSearchResult(
                        title=answer_box.get("title", "Answer"),
                        url=answer_box.get("link", ""),
                        content=answer_box.get("answer", "") or answer_box.get("snippet", ""),
                        score=1.5,  # Higher score for answer box
                    ))

                logger.info(f"Serper search returned {len(results)} results for query: {query[:50]}")
                return results

        except Exception as e:
            logger.error(f"Serper search failed: {e}", exc_info=True)
            return []

    def format_results_as_context(self, results: List[WebSearchResult]) -> str:
        """
        Format web search results as context string for LLM
        
        Args:
            results: List of WebSearchResult objects
            
        Returns:
            Formatted context string
        """
        if not results:
            return ""

        context_parts = ["=== External Knowledge (Web Search) ===\n"]
        
        for idx, result in enumerate(results, 1):
            context_parts.append(f"[Source {idx}] {result.title}")
            if result.url:
                context_parts.append(f"URL: {result.url}")
            context_parts.append(f"Content: {result.content}\n")

        return "\n".join(context_parts)

