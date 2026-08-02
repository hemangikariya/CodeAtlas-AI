import logging
from typing import Dict, Any
from backend.app.mcp.tool_registry import tool_registry
from backend.app.mcp.tool_validator import ToolValidator
from backend.app.guardrails.safety import SafetyGuardrails

logger = logging.getLogger("codeatlas.mcp")


class ToolExecutor:
    """
    Executes MCP tools, checking JSON schemas and executing safety checks on arguments.
    """

    def __init__(self, guardrails: SafetyGuardrails):
        self.guardrails = guardrails
        self.validator = ToolValidator()

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """
        Runs validation and executes the tool.
        """
        tool = tool_registry.get(tool_name)

        # 1. JSON Schema validation
        if not self.validator.validate_args(tool_name, arguments, tool.parameters):
            logger.error(f"Arguments validation failed for tool '{tool_name}'. Args: {arguments}")
            raise ValueError(f"Arguments validation failed for tool '{tool_name}' against schema.")

        # 2. Safety permission validation (e.g. path traversal)
        if not self.guardrails.check_tool_execution(tool_name, arguments):
            logger.error(f"Safety guardrails blocked tool execution for: '{tool_name}'. Args: {arguments}")
            raise PermissionError(f"Security guardrails blocked execution of tool '{tool_name}'.")

        # 3. Execute logic
        logger.info(f"Executing tool '{tool_name}' with arguments: {arguments}")
        try:
            return await tool.execute(arguments, context)
        except Exception as e:
            logger.error(f"Execution of tool '{tool_name}' failed: {str(e)}")
            raise e
