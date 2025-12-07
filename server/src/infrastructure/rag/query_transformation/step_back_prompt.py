"""
StepBackPromptGenerator - Infrastructure Layer
Single Responsibility: Generate step-back prompts for abstract reasoning
"""
from src.infrastructure.llm.openai_client import OpenAIClient


class StepBackPromptGenerator:
    """
    Step-back prompt generator
    Single Responsibility: Generate abstract reasoning prompts
    """

    def __init__(self, llm_client: OpenAIClient):
        self._llm_client = llm_client

    async def generate(self, query: str) -> str:
        """
        Generate step-back prompt for abstract reasoning
        """
        if not query:
            return ""

        system_prompt = (
            "You help reframe detailed questions into higher-level versions "
            "that capture the main intent. The result should aid retrieval of "
            "broader concepts relevant to the original query."
        )
        user_prompt = (
            "Original question:\n"
            f"{query}\n\n"
            "Produce one abstract 'step-back' question that focuses on the core problem."
        )

        response = await self._llm_client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )

        return response.strip() or query

