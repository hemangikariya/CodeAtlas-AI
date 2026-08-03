from typing import Dict, List
from backend.app.copilot.base_generator import BaseGenerator


class GeneratorRegistry:
    """
    Registry management class resolving active Copilot generators by target artifact type.
    """

    def __init__(self):
        self._generators: Dict[str, BaseGenerator] = {}

    def register(self, generator: BaseGenerator) -> None:
        """
        Registers a generator instance.
        """
        self._generators[generator.artifact_type.strip().lower()] = generator

    def get(self, artifact_type: str) -> BaseGenerator:
        """
        Retrieves a generator by type.
        """
        g = self._generators.get(artifact_type.strip().lower())
        if not g:
            raise ValueError(f"No copilot generator found registered for type: '{artifact_type}'.")
        return g

    def list_registered_types(self) -> List[str]:
        """
        Lists all registered generator types.
        """
        return list(self._generators.keys())


# Singleton instance
generator_registry = GeneratorRegistry()
