from typing import Dict
from backend.app.gateway.base_provider import BaseProvider


class ProviderRegistry:
    """
    Registry maintaining configured LLM provider instances.
    """

    def __init__(self):
        self._providers: Dict[str, BaseProvider] = {}

    def register(self, name: str, provider: BaseProvider) -> None:
        self._providers[name.strip().lower()] = provider

    def get(self, name: str) -> BaseProvider:
        prov = self._providers.get(name.strip().lower())
        if not prov:
            raise ValueError(f"LLM Provider '{name}' is not registered.")
        return prov


# Global registry singleton
provider_registry = ProviderRegistry()
