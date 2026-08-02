from typing import Dict, Any, List


class MCPTool:
    """
    Common base interface representing a Model Context Protocol (MCP) tool.
    """
    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {"type": "OBJECT", "properties": {}}
    permissions: List[str] = []
    version: str = "1.0.0"

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """
        Executes the tool logic async.
        'context' dictionary must contain:
        - "knowledge_service": KnowledgeService instance
        - "snapshot_id": str snapshot UUID
        """
        raise NotImplementedError()
