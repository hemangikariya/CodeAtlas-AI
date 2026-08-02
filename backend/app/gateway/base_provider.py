from typing import Dict, Any, List, Optional


class BaseProvider:
    """
    Abstract LLM provider class outlining unified text generation,
    structured output schema formatting, and tool calling operations.
    """

    async def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Performs general dialogue completion, returning text responses or tool call recommendations.
        Returns a dict:
        {
            "text": str,
            "tool_calls": List[Dict[str, Any]], # [{"name": "...", "arguments": {...}}]
            "prompt_tokens": int,
            "completion_tokens": int
        }
        """
        raise NotImplementedError()

    async def generate_structured_output(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        system_instruction: Optional[str] = None,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """
        Guarantees that the LLM response adheres to a specified JSON Schema.
        Returns a dict containing the parsed JSON data under "data".
        """
        raise NotImplementedError()
