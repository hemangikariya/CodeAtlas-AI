from typing import Dict, Any
from backend.app.agents.base_agent import BaseAgent
from backend.app.prompts.prompt_registry import prompt_registry


class DocumentationAgent(BaseAgent):
    """
    Handles docstring checks, onboarding reviews, and comments analyses.
    """

    def __init__(self, gateway, memory):
        super().__init__("DocumentationAgent", gateway, memory)

    async def execute(self, query: str, context: str, tools: list = None) -> Dict[str, Any]:
        prompt = prompt_registry.get_prompt("documentation", context=context, query=query)
        res = await self.gateway.generate(
            prompt=prompt,
            task_type="documentation",
            system_instruction="You are DocumentationAgent, reviews docstrings and READMEs."
        )
        return res

    async def summarize(self, query: str, execution_results: Any) -> str:
        text = execution_results.get("text", "")
        self.memory.add_message("assistant", f"[DocumentationAgent]: {text}")
        return text
