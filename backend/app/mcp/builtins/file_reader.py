from typing import Dict, Any
from backend.app.mcp.tool_schema import MCPTool
from backend.app.mcp.tool_registry import tool_registry


class FileReaderTool(MCPTool):
    name = "FileReader"
    description = "Loads source code contents for a specific repository file path."
    parameters = {
        "type": "OBJECT",
        "properties": {
            "path": {"type": "STRING", "description": "Relative file path of interest."}
        },
        "required": ["path"]
    }
    version = "1.0.0"

    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Any:
        service = context["knowledge_service"]
        snapshot_id = context["snapshot_id"]
        path = arguments["path"]
        content = await service.get_file_content(snapshot_id, path)
        if content is None:
            return {"error": f"File '{path}' could not be loaded or was absent."}
        return {
            "path": path,
            "content": content
        }


tool_registry.register(FileReaderTool())
