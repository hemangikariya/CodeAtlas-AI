from typing import Dict, List
from backend.app.mcp.tool_schema import MCPTool


class ToolRegistry:
    """
    Central storage registry holding registered MCP tools.
    """

    def __init__(self):
        self._tools: Dict[str, MCPTool] = {}

    def register(self, tool: MCPTool) -> None:
        """Registers a tool using its lowercase name key."""
        self._tools[tool.name.strip().lower()] = tool

    def get(self, name: str) -> MCPTool:
        """Loads a registered tool by name."""
        t = self._tools.get(name.strip().lower())
        if not t:
            raise ValueError(f"MCP Tool '{name}' is not registered.")
        return t

    def get_all(self) -> List[MCPTool]:
        """Lists all registered tools."""
        return list(self._tools.values())


# Global tool registry instance
tool_registry = ToolRegistry()

# Proactively import builtins to execute self-registration
import backend.app.mcp.builtins.repo_search
import backend.app.mcp.builtins.graph_search
import backend.app.mcp.builtins.semantic_search
import backend.app.mcp.builtins.file_reader
import backend.app.mcp.builtins.dep_lookup
import backend.app.mcp.builtins.stats_lookup
import backend.app.mcp.builtins.context_builder
