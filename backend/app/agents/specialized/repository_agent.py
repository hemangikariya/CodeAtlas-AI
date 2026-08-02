from typing import Dict, Any
from backend.app.agents.base_agent import BaseAgent
from backend.app.prompts.prompt_registry import prompt_registry


class RepositoryAgent(BaseAgent):
    """
    Handles inquiries about repository structure and layout.
    """

    def __init__(self, gateway, memory):
        super().__init__("RepositoryAgent", gateway, memory)

    async def execute(self, query: str, context: str, tools: list = None) -> Dict[str, Any]:
        prompt = prompt_registry.get_prompt("repository", context=context, query=query)
        res = await self.gateway.generate(
            prompt=prompt,
            task_type="repository",
            system_instruction="You are RepositoryAgent, expert in code repositories structure."
        )
        return res

    async def summarize(self, query: str, execution_results: Any) -> str:
        text = execution_results.get("text", "")
        self.memory.add_message("assistant", f"[RepositoryAgent]: {text}")
        return text
