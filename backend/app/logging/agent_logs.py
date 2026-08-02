import logging
from typing import Dict, Any

agent_logger = logging.getLogger("codeatlas.agent_execution")


class AgentWorkflowLogger:
    """
    Records cognitive pipeline logs: planning, routing, tool executions, gateway token usages.
    """

    @staticmethod
    def log_planner(query: str, plan: Dict[str, Any], latency: float) -> None:
        agent_logger.info(
            f"[Planner Execution] Query: '{query}' | "
            f"Intent: {plan.get('intent')} | Complexity: {plan.get('complexity')} | "
            f"Tasks Count: {len(plan.get('tasks', []))} | Latency: {latency:.3f}s"
        )

    @staticmethod
    def log_routing(agent: str, tool: str, priority: int) -> None:
        agent_logger.info(
            f"[Task Routing] Dispatched task to Specialized Agent: '{agent}' | "
            f"MCP Tool: '{tool}' | Priority: {priority}"
        )

    @staticmethod
    def log_tool(tool: str, args: Dict[str, Any], status: str, latency: float) -> None:
        agent_logger.info(
            f"[Tool Execution] Tool: '{tool}' | Arguments: {args} | "
            f"Status: {status} | Latency: {latency:.3f}s"
        )

    @staticmethod
    def log_gateway(model: str, prompt_tokens: int, completion_tokens: int, latency: float, cost: float) -> None:
        agent_logger.info(
            f"[Gateway Call] Model: '{model}' | Prompt Tokens: {prompt_tokens} | "
            f"Completion Tokens: {completion_tokens} | Latency: {latency:.3f}s | Cost: ${cost:.6f}"
        )

    @staticmethod
    def log_error(component: str, error_message: str) -> None:
        agent_logger.error(
            f"[Execution Error] Component: '{component}' | Message: {error_message}"
        )
