import logging
from typing import Dict, Any, List
from backend.app.memory.memory_manager import MemoryManager
from backend.app.gateway.ai_gateway import AIGateway
from backend.app.mcp.tool_executor import ToolExecutor
from backend.app.knowledge.knowledge_service import KnowledgeService

# Import all specialized agents
from backend.app.agents.specialized.repository_agent import RepositoryAgent
from backend.app.agents.specialized.architecture_agent import ArchitectureAgent
from backend.app.agents.specialized.documentation_agent import DocumentationAgent
from backend.app.agents.specialized.security_agent import SecurityAgent
from backend.app.agents.specialized.quality_agent import QualityAgent
from backend.app.agents.specialized.search_agent import SearchAgent
from backend.app.agents.specialized.analysis_agent import AnalysisAgent

logger = logging.getLogger("codeatlas.agents")


class TaskRouter:
    """
    TaskRouter receives Planner execution plans, dispatches tasks to Specialized Agents,
    runs MCP tool executions, aggregates intermediate reports, and handles errors.
    """

    def __init__(self, gateway: AIGateway, memory: MemoryManager, tool_executor: ToolExecutor):
        self.gateway = gateway
        self.memory = memory
        self.tool_executor = tool_executor
        
        # Agent class mapping
        self._agent_mapping = {
            "repositoryagent": RepositoryAgent,
            "architectureagent": ArchitectureAgent,
            "documentationagent": DocumentationAgent,
            "securityagent": SecurityAgent,
            "qualityagent": QualityAgent,
            "searchagent": SearchAgent,
            "analysisagent": AnalysisAgent
        }

    async def route_and_execute(
        self,
        plan: Dict[str, Any],
        query: str,
        knowledge_service: KnowledgeService,
        snapshot_id: str
    ) -> List[Dict[str, Any]]:
        """
        Sorts planner tasks by priority, runs recommended tools, and collects agent audits.
        """
        tasks = plan.get("tasks", [])
        if not tasks:
            logger.warning("No tasks found in planner plan. Returning empty outputs.")
            return []

        # Sort tasks by priority (ascending)
        sorted_tasks = sorted(tasks, key=lambda x: x.get("priority", 1))
        agent_outputs = []

        context = {
            "knowledge_service": knowledge_service,
            "snapshot_id": snapshot_id
        }

        for task in sorted_tasks:
            agent_name = task.get("agent", "")
            tool_name = task.get("tool", "")
            
            logger.info(f"TaskRouter: Processing task. Agent: {agent_name}, Tool: {tool_name}")

            # 1. Resolve Specialized Agent
            agent_class = self._agent_mapping.get(agent_name.strip().lower())
            if not agent_class:
                logger.warning(f"TaskRouter: Could not resolve Specialized Agent named: '{agent_name}'. Skipping.")
                continue

            agent_instance = agent_class(self.gateway, self.memory)

            # 2. Run MCP Tool
            tool_output = ""
            if tool_name:
                try:
                    # Formulate arguments
                    args = task.get("arguments") or {}
                    if not isinstance(args, dict):
                        args = {}
                    
                    # Merge with default fallback queries if required parameters are missing
                    if "query" not in args and tool_name in ["RepositorySearch", "SemanticSearch", "ContextBuilder"]:
                        args["query"] = query
                    if "path" not in args and tool_name == "FileReader":
                        # If file reader is requested without a path, fallback to search files or retrieve stats
                        files = await knowledge_service.search_files(snapshot_id, "")
                        if files:
                            args["path"] = files[0]["path"]
                        else:
                            args["path"] = "main.py"
                            
                    res = await self.tool_executor.execute_tool(tool_name, args, context)
                    tool_output = str(res)
                except Exception as e:
                    logger.error(f"TaskRouter: Tool '{tool_name}' failed to execute: {str(e)}")
                    tool_output = f"[Tool {tool_name} failed: {str(e)}]"

            # 3. Invoke Specialized Agent reasoning
            try:
                agent_res = await agent_instance.execute(
                    query=query,
                    context=tool_output,
                    tools=[task]
                )
                report = await agent_instance.summarize(query, agent_res)
                agent_outputs.append({
                    "agent": agent_name,
                    "report": report
                })
            except Exception as e:
                logger.error(f"TaskRouter: Agent '{agent_name}' failed: {str(e)}")
                agent_outputs.append({
                    "agent": agent_name,
                    "report": f"[Agent analysis failed: {str(e)}]"
                })

        return agent_outputs
