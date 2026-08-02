import re
import logging

logger = logging.getLogger("codeatlas.guardrails")


class OutputValidator:
    """
    Validates and sanitizes agent generated outputs, preventing credentials exposure or unsafe elements.
    """

    def __init__(self):
        # Match common password/token keys: e.g., secret_key = "abc"
        self.secret_patterns = [
            re.compile(r"api_key\s*=\s*['\"][a-zA-Z0-9_\-]{16,}['\"]", re.IGNORECASE),
            re.compile(r"secret_key\s*=\s*['\"][a-zA-Z0-9_\-]{16,}['\"]", re.IGNORECASE),
            re.compile(r"password\s*=\s*['\"][a-zA-Z0-9_\-]{8,}['\"]", re.IGNORECASE),
            re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE)
        ]

    def validate_and_sanitize(self, output_text: str) -> str:
        """
        Sanitizes sensitive information from generated text outputs.
        """
        if not output_text:
            return ""

        sanitized = output_text
        for pattern in self.secret_patterns:
            if pattern.search(sanitized):
                logger.warning("Secret API token or password pattern detected in output. Redacting.")
                sanitized = pattern.sub("[REDACTED_SENSITIVE_KEY]", sanitized)

        # Basic validation check for harmful content
        if "rm -rf" in sanitized.lower() and "sudo" in sanitized.lower():
            logger.warning("Dangerous command detected in generated output text. Sanitizing code suggestions.")
            sanitized = sanitized.replace("rm -rf", "echo '[blocked command]'")

        return sanitized
