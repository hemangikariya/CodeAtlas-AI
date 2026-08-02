import logging

logger = logging.getLogger("codeatlas.guardrails")


class ToolPermissionValidator:
    """
    Validates tool execution parameters to prevent path traversal or out-of-scope executions.
    """

    def validate_tool_args(self, tool_name: str, arguments: dict) -> bool:
        """
        Enforces constraints on inputs like file path names or search bounds.
        """
        # 1. Path traversal protection on FileReader or similar tools
        path_arg = arguments.get("path") or arguments.get("file_path") or arguments.get("target")
        if path_arg and isinstance(path_arg, str):
            normalized = path_arg.replace("\\", "/")
            # Block relative traversals or root paths
            if ".." in normalized or normalized.startswith("/") or (len(normalized) > 1 and normalized[1] == ":"):
                logger.warning(f"Tool validation blocked suspicious path input: '{path_arg}' for tool '{tool_name}'")
                return False

        # 2. Limit top_k lookup boundaries to prevent resource exhaustion
        top_k = arguments.get("top_k")
        if top_k is not None:
            try:
                k_val = int(top_k)
                if k_val <= 0 or k_val > 50:
                    arguments["top_k"] = 10 # Force safe default limits
            except Exception:
                arguments["top_k"] = 5

        return True
