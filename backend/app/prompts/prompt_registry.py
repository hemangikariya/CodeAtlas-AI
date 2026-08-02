from backend.app.prompts.prompt_loader import PromptLoader


class PromptRegistry:
    """
    Centralized registry managing prompt loader access.
    """

    def __init__(self):
        self.loader = PromptLoader()

    def get_prompt(self, name: str, **kwargs) -> str:
        """
        Formats a system prompt template.
        """
        return self.loader.format_prompt(name, **kwargs)

    def get_template(self, name: str) -> str:
        """
        Gets the raw template string.
        """
        return self.loader.load_template(name)


# Global registry singleton
prompt_registry = PromptRegistry()
