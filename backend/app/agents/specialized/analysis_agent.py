from typing import Dict, Any
from backend.app.agents.base_agent import BaseAgent
from backend.app.prompts.prompt_registry import prompt_registry


class AnalysisAgent(BaseAgent):
    """
    Handles inquiries about control flow branches and logic densities.
    """

    def __init__(self, gateway, memory):
        super().__init__("AnalysisAgent", gateway, memory)

    async def execute(self, query: str, context: str, tools: list = None) -> Dict[str, Any]:
        prompt = prompt_registry.get_prompt("analysis", context=context, query=query)
        res = await self.gateway.generate(
            prompt=prompt,
            task_type="analysis",
            system_instruction="You are AnalysisAgent, expert in evaluating logical branches."
        )
        return res

    async def summarize(self, query: str, execution_results: Any) -> str:
        text = execution_results.get("text", "")
        self.memory.add_message("assistant", f"[AnalysisAgent]: {text}")
        return text
