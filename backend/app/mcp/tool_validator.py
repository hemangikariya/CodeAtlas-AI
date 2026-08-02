from typing import Dict, Any
from backend.app.guardrails.json_validator import JSONSchemaValidator


class ToolValidator:
    """
    Validates MCP tool arguments against defined JSON schemas.
    """

    def __init__(self):
        self.validator = JSONSchemaValidator()

    def validate_args(self, tool_name: str, arguments: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        Validates argument schema compliance.
        """
        # Ensure arguments is a dict
        if not isinstance(arguments, dict):
            return False
            
        # Call the schema validator
        return self.validator.validate(arguments, schema)
