"""
LLMGenerator - Infrastructure Layer
Single Responsibility: Generate answers using LLM
"""
from typing import List, Optional
from src.infrastructure.llm.openai_client import OpenAIClient
from src.infrastructure.services.token_tracker import TokenTracker
from src.config.settings import get_settings

settings = get_settings()


class LLMGenerator:
    """
    LLM-based answer generator
    Single Responsibility: Generate final answers from context
    """

    def __init__(self, llm_client: OpenAIClient, token_tracker: Optional[TokenTracker] = None):
        self._llm_client = llm_client
        self._token_tracker = token_tracker
        self._max_tokens = settings.max_tokens
        self._temperature = settings.temperature

    async def generate(
        self, 
        query: str, 
        context: str, 
        external_context: str = "",
        conversation_history: List = None,
    ) -> str:
        """
        Generate answer from query, internal context, optional external context, and conversation history
        
        Args:
            query: User's question
            context: Internal context from uploaded documents
            external_context: External context from web search (optional)
            conversation_history: Previous messages in the conversation (optional)
        """
        if not query:
            return ""

        sanitized_internal = context.strip() if context else ""
        sanitized_external = external_context.strip() if external_context else ""
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"LLM Generation - Internal context length: {len(sanitized_internal)}, External context length: {len(sanitized_external)}")
        if sanitized_internal:
            logger.info(f"Internal context preview (first 500 chars): {sanitized_internal[:500]}")
        else:
            logger.error("CRITICAL: Internal context is EMPTY - no chunks retrieved! This means the document was not found or query doesn't match.")
            logger.error("This could indicate:")
            logger.error("1. Document was not indexed properly")
            logger.error("2. Query embedding doesn't match document embeddings")
            logger.error("3. Group filter might be excluding the document")

        combined_context_parts = []
        
        if sanitized_internal:
            combined_context_parts.append("=== Internal Knowledge (Your Documents) ===\n")
            combined_context_parts.append(sanitized_internal)
        
        if sanitized_external:
            combined_context_parts.append("\n\n")
            combined_context_parts.append(sanitized_external)

        combined_context = "\n".join(combined_context_parts) if combined_context_parts else ""
        
        if not combined_context:
            combined_context = "No supporting context was retrieved."

        system_prompt = (
            "You are a helpful assistant that answers questions using the user's uploaded documents.\n\n"
            "**CRITICAL RULE: If DOCUMENT CONTENT section exists, it ALWAYS contains relevant information.**\n\n"
            "**PRIORITY 1: Internal Knowledge (Your Documents) - MANDATORY FIRST AND ONLY**\n"
            "- If '=== Internal Knowledge (Your Documents) ===' section contains ANY text, that text IS the answer\n"
            "- The presence of text in DOCUMENT CONTENT means there IS information - NEVER say 'no specific text' or 'doesn't contain'\n"
            "- You MUST read and use ALL the text in DOCUMENT CONTENT to answer the question\n"
            "- Start your answer with: 'According to your uploaded documents...' or 'Based on the documents you provided...'\n"
            "- Quote or paraphrase information from DOCUMENT CONTENT directly\n"
            "- These documents override ALL other sources (your training knowledge AND web search)\n"
            "- If DOCUMENT CONTENT mentions dates, events, facts - those ARE the answers, use them\n"
            "- **IF DOCUMENT CONTENT EXISTS, IGNORE EXTERNAL KNOWLEDGE (Web Search) COMPLETELY**\n"
            "- **IF DOCUMENT CONTENT EXISTS, IGNORE YOUR TRAINING KNOWLEDGE IF IT CONTRADICTS**\n\n"
            "**PRIORITY 2: Your General Knowledge (Training Data) - ONLY if DOCUMENT CONTENT is empty**\n"
            "- Use your general knowledge ONLY if DOCUMENT CONTENT section is completely empty\n"
            "- If DOCUMENT CONTENT has text, DO NOT use general knowledge\n"
            "- NEVER use general knowledge INSTEAD of DOCUMENT CONTENT\n\n"
            "**PRIORITY 3: External Knowledge (Web Search) - ONLY if DOCUMENT CONTENT is empty**\n"
            "- Use web search ONLY if DOCUMENT CONTENT section is completely empty\n"
            "- If DOCUMENT CONTENT has text, you MUST IGNORE web search results completely\n"
            "- **IF DOCUMENT CONTENT EXISTS, DO NOT MENTION OR USE ANY INFORMATION FROM WEB SEARCH**\n"
            "- Web search is ONLY a fallback when no documents are available\n\n"
            "**FORBIDDEN PHRASES - NEVER SAY:**\n"
            "- 'There is no specific text'\n"
            "- 'Doesn't directly answer'\n"
            "- 'Doesn't contain'\n"
            "- 'No relevant information'\n"
            "- If DOCUMENT CONTENT has text, these phrases are WRONG - the text IS the information\n\n"
            "**STRICT GUIDELINES:**\n"
            "- If DOCUMENT CONTENT section exists and has text, you MUST use it\n"
            "- Read ALL content, not just the first paragraph\n"
            "- Combine information from multiple sections if needed\n"
            "- Answer naturally - write as if you're summarizing a book, NOT analyzing technical chunks\n"
            "- NEVER mention chunks, chunk numbers, document structure, or technical metadata\n"
            "- If documents contradict your knowledge, TRUST THE DOCUMENTS\n"
            "- **IF DOCUMENT CONTENT EXISTS, YOUR ANSWER MUST BE BASED ONLY ON DOCUMENT CONTENT**"
        )
        
        user_prompt_parts = []
        
        if sanitized_internal:
            user_prompt_parts.append("=" * 80)
            user_prompt_parts.append("=== Internal Knowledge (Your Documents) ===")
            user_prompt_parts.append("=" * 80)
            user_prompt_parts.append("")
            user_prompt_parts.append("IMPORTANT: The content below is EXTRACTED TEXT from your uploaded documents.")
            user_prompt_parts.append("This is the PRIMARY and MOST AUTHORITATIVE source. You MUST use this information FIRST.")
            user_prompt_parts.append("")
            user_prompt_parts.append("DOCUMENT CONTENT:")
            user_prompt_parts.append("")
            user_prompt_parts.append(sanitized_internal)
            user_prompt_parts.append("")
            user_prompt_parts.append("=" * 80)
            user_prompt_parts.append("")
        else:
            user_prompt_parts.append("=" * 80)
            user_prompt_parts.append("=== Internal Knowledge (Your Documents) ===")
            user_prompt_parts.append("=" * 80)
            user_prompt_parts.append("")
            user_prompt_parts.append("WARNING: DOCUMENT CONTENT section is EMPTY.")
            user_prompt_parts.append("This means no documents were found matching the query.")
            user_prompt_parts.append("Possible reasons:")
            user_prompt_parts.append("1. No documents uploaded to the selected group")
            user_prompt_parts.append("2. Documents not indexed yet")
            user_prompt_parts.append("3. Query doesn't match document content")
            user_prompt_parts.append("")
            user_prompt_parts.append("DOCUMENT CONTENT:")
            user_prompt_parts.append("(EMPTY - No document content available)")
            user_prompt_parts.append("")
            user_prompt_parts.append("=" * 80)
            user_prompt_parts.append("")
        
        if sanitized_external:
            user_prompt_parts.append("=" * 80)
            user_prompt_parts.append("=== External Knowledge (Web Search) - IGNORE IF DOCUMENT CONTENT EXISTS ===")
            user_prompt_parts.append("=" * 80)
            user_prompt_parts.append("")
            user_prompt_parts.append("**CRITICAL: If DOCUMENT CONTENT section above has ANY text, you MUST IGNORE this section completely.**")
            user_prompt_parts.append("**Only use this section if DOCUMENT CONTENT is completely empty.**")
            user_prompt_parts.append("")
            user_prompt_parts.append(sanitized_external)
            user_prompt_parts.append("")
            user_prompt_parts.append("=" * 80)
            user_prompt_parts.append("")
        
        if conversation_history and len(conversation_history) > 0:
            user_prompt_parts.append("=" * 80)
            user_prompt_parts.append("=== Previous Conversation ===")
            user_prompt_parts.append("=" * 80)
            user_prompt_parts.append("")
            recent_messages = conversation_history[-6:]
            for msg in recent_messages:
                role_label = "User" if msg.role == "user" else "Assistant"
                user_prompt_parts.append(f"{role_label}: {msg.content[:200]}{'...' if len(msg.content) > 200 else ''}")
            user_prompt_parts.append("")
            user_prompt_parts.append("=" * 80)
            user_prompt_parts.append("")
            user_prompt_parts.append("NOTE: If the current question refers to 'above question', 'more details', etc.,")
            user_prompt_parts.append("it refers to the previous conversation above. Use that context to understand what the user is asking.")
            user_prompt_parts.append("")
        
        user_prompt_parts.append(f"User question: {query}")
        user_prompt_parts.append("")
        user_prompt_parts.append(
            "CRITICAL INSTRUCTIONS - FOLLOW THESE RULES EXACTLY:\n\n"
            "**RULE 1: DOCUMENT CONTENT = ANSWER EXISTS**\n"
            "- The 'DOCUMENT CONTENT' section above contains REAL TEXT extracted from the user's PDF/document\n"
            "- If this section has ANY text, it means there IS information that answers the question\n"
            "- You MUST use this text to answer - it IS the answer\n\n"
            "**RULE 2: FORBIDDEN PHRASES - NEVER USE THESE**\n"
            "- 'There is no specific text' ❌ FORBIDDEN\n"
            "- 'Doesn't directly answer' ❌ FORBIDDEN\n"
            "- 'Doesn't contain' ❌ FORBIDDEN\n"
            "- 'No relevant information' ❌ FORBIDDEN\n"
            "- 'The documents don't provide' ❌ FORBIDDEN\n"
            "- 'Chunk #1', 'Chunk #2', 'chunk #3', etc. ❌ FORBIDDEN - NEVER mention chunk numbers\n"
            "- 'DOCUMENT CONTENT chunk', 'chunk does not', 'chunk mentions' ❌ FORBIDDEN\n"
            "- Any reference to chunks, chunk numbers, or document structure ❌ FORBIDDEN\n"
            "- If DOCUMENT CONTENT has text, these phrases are WRONG - delete them from your response\n\n"
            "**RULE 3: HOW TO ANSWER**\n"
            "- Start with: 'According to your uploaded documents...' or 'Based on the documents you provided...'\n"
            "- Read ALL content in DOCUMENT CONTENT section\n"
            "- Extract and combine information from the document text\n"
            "- If the document says 'Football arose in England in the middle of the 19th century' → INCLUDE IT\n"
            "- If the document mentions dates (1863, 1885, 1930) → INCLUDE THEM\n"
            "- If the document mentions organizations (FIFA, Football Association) → INCLUDE THEM\n"
            "- If the document mentions events, history, evolution → INCLUDE ALL\n"
            "- Answer naturally as if you're reading from a book - NO technical references to chunks\n"
            "- **IF DOCUMENT CONTENT EXISTS, DO NOT MENTION OR USE ANY INFORMATION FROM EXTERNAL KNOWLEDGE (Web Search)**\n"
            "- **IF DOCUMENT CONTENT EXISTS, DO NOT MENTION OR USE ANY INFORMATION FROM YOUR TRAINING DATA IF IT CONTRADICTS**\n\n"
            "**RULE 4: EXAMPLE**\n"
            "- Question: 'History of Football'\n"
            "- DOCUMENT CONTENT: 'Football arose in England in the middle of the 19th century'\n"
            "- Your answer MUST start: 'According to your uploaded documents, football arose in England in the middle of the 19th century...'\n"
            "- DO NOT say: 'Chunk #1 mentions...' or 'The document content chunk...' - that's WRONG\n"
            "- DO NOT say: 'There is no specific text' - that's WRONG\n\n"
            "**REMEMBER: If DOCUMENT CONTENT section exists and has text, you HAVE the answer. Use it.**"
        )
        
        user_prompt = "\n".join(user_prompt_parts)

        response = await self._llm_client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            token_tracker=self._token_tracker,
        )

        return response.strip()

