from typing import Dict, Any
from backend.app.agents.base_agent import BaseAgent
from backend.app.prompts.prompt_registry import prompt_registry


class SecurityAgent(BaseAgent):
    """
    Handles vulnerability checks and secure programming patterns evaluations.
    """

    def __init__(self, gateway, memory):
        super().__init__("SecurityAgent", gateway, memory)

    async def execute(self, query: str, context: str, tools: list = None) -> Dict[str, Any]:
        prompt = prompt_registry.get_prompt("security", context=context, query=query)
        res = await self.gateway.generate(
            prompt=prompt,
            task_type="security",
            system_instruction="You are SecurityAgent, analyzing code vulnerability markers."
        )
        return res

    async def summarize(self, query: str, execution_results: Any) -> str:
        text = execution_results.get("text", "")
        self.memory.add_message("assistant", f"[SecurityAgent]: {text}")
        return text
