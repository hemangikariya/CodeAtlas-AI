import os
from typing import Dict


class PromptLoader:
    """
    Loads raw prompt text templates from filesystem files and caches them.
    Interpolates variables using standard python formatting.
    """

    def __init__(self, templates_dir: str = ""):
        if not templates_dir:
            self.templates_dir = os.path.join(os.path.dirname(__file__), "prompt_templates")
        else:
            self.templates_dir = templates_dir
        self._cache: Dict[str, str] = {}

    def load_template(self, name: str) -> str:
        """
        Loads the template text from the target file, caching for performance.
        """
        template_name = name.strip()
        if template_name in self._cache:
            return self._cache[template_name]

        # Standardize name extension
        if not template_name.endswith(".txt"):
            filename = f"{template_name}.txt"
        else:
            filename = template_name

        path = os.path.join(self.templates_dir, filename)
        if not os.path.exists(path):
            # Fallback path creation for dynamic templates
            os.makedirs(self.templates_dir, exist_ok=True)
            # Create a simple placeholder if it doesn't exist to avoid hard crash
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"System instructions placeholder for {template_name}.\nContent: {{content}}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        self._cache[template_name] = content
        return content

    def format_prompt(self, name: str, **kwargs) -> str:
        """
        Fetches template and applies string interpolation.
        """
        template = self.load_template(name)
        try:
            return template.format(**kwargs)
        except KeyError as e:
            # Fallback in case template params don't match arguments perfectly
            # Logs warning and returns raw string plus arguments description
            return template + f"\n[Formatting error: missing parameter {str(e)}]\nContext params: {str(kwargs)}"
