from typing import Dict, Any
from backend.app.agents.base_agent import BaseAgent
from backend.app.prompts.prompt_registry import prompt_registry


class SearchAgent(BaseAgent):
    """
    Handles similarity lookup list queries and simple keywords mapping files.
    """

    def __init__(self, gateway, memory):
        super().__init__("SearchAgent", gateway, memory)

    async def execute(self, query: str, context: str, tools: list = None) -> Dict[str, Any]:
        prompt = prompt_registry.get_prompt("search", context=context, query=query)
        res = await self.gateway.generate(
            prompt=prompt,
            task_type="search",
            system_instruction="You are SearchAgent, identifying code similarities and files."
        )
        return res

    async def summarize(self, query: str, execution_results: Any) -> str:
        text = execution_results.get("text", "")
        self.memory.add_message("assistant", f"[SearchAgent]: {text}")
        return text
