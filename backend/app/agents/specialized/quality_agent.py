from typing import Dict, Any
from backend.app.agents.base_agent import BaseAgent
from backend.app.prompts.prompt_registry import prompt_registry


class QualityAgent(BaseAgent):
    """
    Handles evaluations on code complexity, style consistency, and duplication.
    """

    def __init__(self, gateway, memory):
        super().__init__("QualityAgent", gateway, memory)

    async def execute(self, query: str, context: str, tools: list = None) -> Dict[str, Any]:
        prompt = prompt_registry.get_prompt("quality", context=context, query=query)
        res = await self.gateway.generate(
            prompt=prompt,
            task_type="quality",
            system_instruction="You are QualityAgent, reviews refactoring targets and code metrics."
        )
        return res

    async def summarize(self, query: str, execution_results: Any) -> str:
        text = execution_results.get("text", "")
        self.memory.add_message("assistant", f"[QualityAgent]: {text}")
        return text
