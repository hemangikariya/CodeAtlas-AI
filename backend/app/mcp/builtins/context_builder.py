from typing import Dict, Any
from backend.app.mcp.tool_schema import MCPTool
from backend.app.mcp.tool_registry import tool_registry


class ContextBuilderTool(MCPTool):
    name = "ContextBuilder"
    description = "Assembles similarity-retrieved code snippets into a token bounded context block."
    parameters = {
        "type": "OBJECT",
        "properties": {
            "query": {"type": "STRING", "description": "Search query indicating target matching features."},
            "search_type": {"type": "STRING", "description": "Intent classification (ALL, CLASS, FUNCTION, API)."},
            "token_limit": {"type": "INTEGER", "description": "Target context window token limit limit."}
        },
        "required": ["query"]
    }
    version = "1.0.0"

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Any:
        service = context["knowledge_service"]
        snapshot_id = context["snapshot_id"]
        query = arguments["query"]
        stype = arguments.get("search_type", "ALL")
        limit = arguments.get("token_limit", 4000)
        return await service.get_context(
            snapshot_id=snapshot_id,
            query=query,
            search_type=stype,
            token_limit=limit
        )


tool_registry.register(ContextBuilderTool())
