import logging
from backend.app.gateway.ai_gateway import AIGateway
from backend.app.prompts.prompt_registry import prompt_registry

logger = logging.getLogger("codeatlas.guardrails")


class PromptValidator:
    """
    Validates input query prompts, detecting injection attempts or dangerous instructions.
    """

    def __init__(self, gateway: AIGateway):
        self.gateway = gateway

    async def validate(self, prompt: str) -> bool:
        """
        Runs rules and heuristic checks, followed by LLM-based safety verification.
        """
        if not prompt:
            return True

        lower_prompt = prompt.lower()

        # 1. Heuristics check
        malicious_patterns = [
            "ignore previous instructions",
            "ignore all instructions",
            "system override",
            "bypass system",
            "rm -rf /",
            "format c:"
        ]
        for pattern in malicious_patterns:
            if pattern in lower_prompt:
                logger.warning(f"Heuristics blocked input prompt containing: '{pattern}'")
                return False

        # 2. LLM-based structured safety query
        try:
            safety_prompt = prompt_registry.get_prompt("safety_guardrail", content=prompt)
            schema = {
                "type": "OBJECT",
                "properties": {
                    "is_safe": {"type": "BOOLEAN"},
                    "reason": {"type": "STRING"},
                    "confidence": {"type": "NUMBER"}
                },
                "required": ["is_safe", "reason", "confidence"]
            }
            res = await self.gateway.generate_structured(
                prompt=safety_prompt,
                response_schema=schema,
                task_type="safety"
            )
            is_safe = res.get("data", {}).get("is_safe", True)
            if not is_safe:
                reason = res.get("data", {}).get("reason", "Unknown injection/safety risk.")
                logger.warning(f"LLM safety check blocked prompt. Reason: {reason}")
            return is_safe
        except Exception as e:
            logger.error(f"LLM prompt safety check encountered error: {str(e)}. Defaulting to safe=True.")
            return True
