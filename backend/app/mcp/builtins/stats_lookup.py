from typing import Dict, Any
from backend.app.mcp.tool_schema import MCPTool
from backend.app.mcp.tool_registry import tool_registry


class StatisticsLookupTool(MCPTool):
    name = "StatisticsLookup"
    description = "Retrieves Knowledge Graph stats (nodes count, edges count, average degree, components)."
    parameters = {
        "type": "OBJECT",
        "properties": {}
    }
    version = "1.0.0"

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Any:
        service = context["knowledge_service"]
        snapshot_id = context["snapshot_id"]
        return await service.get_statistics(snapshot_id)


tool_registry.register(StatisticsLookupTool())
