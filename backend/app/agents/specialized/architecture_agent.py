from typing import Dict, Any
from backend.app.agents.base_agent import BaseAgent
from backend.app.prompts.prompt_registry import prompt_registry


class ArchitectureAgent(BaseAgent):
    """
    Handles inquiries about design patterns, imports, relationships, and code dependencies.
    """

    def __init__(self, gateway, memory):
        super().__init__("ArchitectureAgent", gateway, memory)

    async def execute(self, query: str, context: str, tools: list = None) -> Dict[str, Any]:
        prompt = prompt_registry.get_prompt("architecture", context=context, query=query)
        res = await self.gateway.generate(
            prompt=prompt,
            task_type="architecture",
            system_instruction="You are ArchitectureAgent, expert in system layouts and imports."
        )
        return res

    async def summarize(self, query: str, execution_results: Any) -> str:
        text = execution_results.get("text", "")
        self.memory.add_message("assistant", f"[ArchitectureAgent]: {text}")
        return text
