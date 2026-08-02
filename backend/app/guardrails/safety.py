from typing import Dict, Any, Optional
from backend.app.gateway.ai_gateway import AIGateway
from backend.app.guardrails.prompt_validator import PromptValidator
from backend.app.guardrails.output_validator import OutputValidator
from backend.app.guardrails.tool_permission import ToolPermissionValidator
from backend.app.guardrails.json_validator import JSONSchemaValidator


class SafetyGuardrails:
    """
    Coordinated facade for Prompt, Tool, and Output safety validations.
    """

    def __init__(self, gateway: AIGateway):
        self.prompt_validator = PromptValidator(gateway)
        self.output_validator = OutputValidator()
        self.tool_validator = ToolPermissionValidator()
        self.json_validator = JSONSchemaValidator()

    async def check_input_prompt(self, prompt: str) -> bool:
        """
        Stage 1: Prompt Safety checks.
        """
        return await self.prompt_validator.validate(prompt)

    def check_tool_execution(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """
        Stage 2: Tool Parameter security checks.
        """
        return self.tool_validator.validate_tool_args(tool_name, arguments)

    def sanitize_response(self, text: str) -> str:
        """
        Stage 3: Output sanitization and leak protection.
        """
        return self.output_validator.validate_and_sanitize(text)

    def validate_json_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        Ensures structured JSON conformances.
        """
        return self.json_validator.validate(data, schema)
