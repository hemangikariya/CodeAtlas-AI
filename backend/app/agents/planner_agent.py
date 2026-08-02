import logging
from typing import Dict, Any
from backend.app.gateway.ai_gateway import AIGateway
from backend.app.prompts.prompt_registry import prompt_registry

logger = logging.getLogger("codeatlas.agents")


class PlannerAgent:
    """
    Planner agent responsible for analyzing user intent and formulating structured subtasks list.
    Planner Agent never executes tools directly.
    """

    def __init__(self, gateway: AIGateway):
        self.gateway = gateway

    async def create_plan(self, query: str) -> Dict[str, Any]:
        """
        Generates structured subtasks execution plans.
        """
        logger.info(f"Planner Agent starting analysis on request: '{query}'")
        
        prompt = prompt_registry.get_prompt("planner", query=query)
        schema = {
            "type": "OBJECT",
            "properties": {
                "intent": {"type": "STRING", "description": "Classified request intent."},
                "complexity": {"type": "STRING", "description": "Complexity bounds: low, medium, or high."},
                "tasks": {
                    "type": "ARRAY",
                    "description": "List of subtasks to delegate to specialized agents.",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "agent": {"type": "STRING", "description": "Name of target Specialized Agent class."},
                            "tool": {"type": "STRING", "description": "Target MCP tool name recommendation."},
                            "priority": {"type": "INTEGER", "description": "Order of execution sequence."},
                            "arguments": {"type": "OBJECT", "description": "Optional arguments map for the tool execution."}
                        },
                        "required": ["agent", "tool", "priority"]
                    }
                }
            },
            "required": ["intent", "complexity", "tasks"]
        }

        try:
            res = await self.gateway.generate_structured(
                prompt=prompt,
                response_schema=schema,
                task_type="planning"
            )
            plan = res.get("data", {})
            logger.info(f"Planner Agent successfully formed plan. Intent: {plan.get('intent')}, Tasks count: {len(plan.get('tasks', []))}")
            return plan
        except Exception as e:
            logger.error(f"Planner Agent encountered execution error: {str(e)}")
            # Fail-safe default plan fallback
            return {
                "intent": "general_inquiry",
                "complexity": "low",
                "tasks": [
                    {
                        "agent": "SearchAgent",
                        "tool": "SemanticSearch",
                        "priority": 1
                    }
                ]
            }
        
    def validate_plan(self, plan: Dict[str, Any]) -> bool:
        """
        Asserts correctness of generated execution subtasks.
        """
        if not plan or "tasks" not in plan or not plan["tasks"]:
            return False
        for t in plan["tasks"]:
            if "agent" not in t or "tool" not in t:
                return False
        return True
