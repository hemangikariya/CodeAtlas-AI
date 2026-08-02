from typing import Dict, Any
from backend.app.mcp.tool_schema import MCPTool
from backend.app.mcp.tool_registry import tool_registry


class RepositorySearchTool(MCPTool):
    name = "RepositorySearch"
    description = "Finds files matching keyword patterns in the repository's path directory."
    parameters = {
        "type": "OBJECT",
        "properties": {
            "query": {"type": "STRING", "description": "String query pattern matching path segment name."}
        },
        "required": ["query"]
    }
    version = "1.0.0"

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Any:
        service = context["knowledge_service"]
        snapshot_id = context["snapshot_id"]
        query = arguments["query"]
        return await service.search_files(snapshot_id, query)


# Register tool singleton
tool_registry.register(RepositorySearchTool())
