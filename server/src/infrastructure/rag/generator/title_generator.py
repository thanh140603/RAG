"""
TitleGenerator - Infrastructure Layer
Single Responsibility: Generate chat session titles from conversation
"""
from typing import Optional
from src.infrastructure.llm.openai_client import OpenAIClient
from src.infrastructure.services.token_tracker import TokenTracker


class TitleGenerator:
    """
    Generate concise titles for chat sessions based on first question and answer
    """

    def __init__(self, llm_client: OpenAIClient, token_tracker: Optional[TokenTracker] = None):
        self._llm_client = llm_client
        self._token_tracker = token_tracker

    async def generate(self, question: str, answer: str) -> str:
        """
        Generate a concise title (max 50 chars) from question and answer
        
        Args:
            question: First user question
            answer: First assistant response
            
        Returns:
            Concise title (max 50 characters)
        """
        if not question or not answer:
            return "New Chat"
        
        question_preview = question[:200] if len(question) > 200 else question
        answer_preview = answer[:300] if len(answer) > 300 else answer
        
        prompt = f"""Generate a concise title (maximum 50 characters) for a chat conversation based on the following:

Question: {question_preview}
Answer: {answer_preview}

Requirements:
- Title should be concise and descriptive (max 50 characters)
- Should capture the main topic or subject
- Use natural language, no quotes or special formatting
- If the question is in Vietnamese, the title can be in Vietnamese
- Return ONLY the title, nothing else

Title:"""

        try:
            response = await self._llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates concise, descriptive titles for chat conversations."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=50,
                token_tracker=self._token_tracker,
            )
            
            title = response.strip()
            title = title.strip('"\'')
            if len(title) > 50:
                title = title[:47] + "..."
            
            return title if title else "New Chat"
        except Exception:
            fallback = question[:47] + "..." if len(question) > 50 else question
            return fallback if fallback else "New Chat"

