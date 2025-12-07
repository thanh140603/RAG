"""
VLLMClient - Infrastructure Layer
Single Responsibility: Interface with vLLM API
"""
from typing import List
import httpx
from src.config.settings import get_settings

settings = get_settings()


class VLLMClient:
    """
    vLLM API client
    Single Responsibility: Handle vLLM API interactions
    """
    
    def __init__(self):
        self._base_url = settings.vllm_base_url
        self._model = settings.vllm_model_name
        self._client = httpx.AsyncClient(base_url=self._base_url)
    
    async def chat_completion(self, messages: List[dict]) -> str:
        """
        Generate chat completion using vLLM
        """
        # TODO: Implement vLLM chat completion
        # response = await self._client.post(
        #     "/v1/chat/completions",
        #     json={
        #         "model": self._model,
        #         "messages": messages
        #     }
        # )
        # return response.json()["choices"][0]["message"]["content"]
        return ""

