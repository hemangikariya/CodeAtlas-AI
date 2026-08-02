from typing import Dict, Any, List
from backend.app.gateway.ai_gateway import AIGateway
from backend.app.memory.memory_manager import MemoryManager


class BaseAgent:
    """
    Common base agent class defining operational contracts (plan, execute, validate, summarize).
    All specialized agents inherit from this class.
    """

    def __init__(self, name: str, gateway: AIGateway, memory: MemoryManager):
        self.name = name
        self.gateway = gateway
        self.memory = memory

    async def plan(self, query: str, context: str) -> List[Dict[str, Any]]:
        """
        Determines the internal execution steps.
        """
        return []

    async def execute(self, query: str, context: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Runs agent reasoning, formatting instructions, and recommending tool executions if needed.
        """
        raise NotImplementedError()

    async def validate(self, output: str) -> bool:
        """
        Validates output completeness.
        """
        return True

    async def summarize(self, query: str, execution_results: Any) -> str:
        """
        Summarizes tool executions and reasoning into an intermediate report.
        """
        raise NotImplementedError()
