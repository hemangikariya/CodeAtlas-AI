from typing import Dict, Any
from backend.app.mcp.tool_schema import MCPTool
from backend.app.mcp.tool_registry import tool_registry


class SemanticSearchTool(MCPTool):
    name = "SemanticSearch"
    description = "Queries cosine similarity matching lists on repository code chunk embeddings."
    parameters = {
        "type": "OBJECT",
        "properties": {
            "query": {"type": "STRING", "description": "Semantic query string description."},
            "search_type": {"type": "STRING", "description": "Filter class, e.g. 'ALL', 'CLASS', 'FUNCTION', 'API'."},
            "top_k": {"type": "INTEGER", "description": "Number of similarity results to return."}
        },
        "required": ["query"]
    }
    version = "1.0.0"

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Any:
        service = context["knowledge_service"]
        snapshot_id = context["snapshot_id"]
        query = arguments["query"]
        stype = arguments.get("search_type", "ALL")
        top_k = arguments.get("top_k", 5)
        return await service.search(snapshot_id, query, search_type=stype, top_k=top_k)


tool_registry.register(SemanticSearchTool())
