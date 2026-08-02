from backend.app.core.config import settings
from backend.app.gateway.gemini_provider import GeminiProvider
from backend.app.gateway.provider_registry import provider_registry, ProviderRegistry
from backend.app.gateway.base_provider import BaseProvider


class ProviderFactory:
    """
    Factory resolving LLM connections.
    """

    @staticmethod
    def get_provider(provider_name: str = "gemini", model_name: str = "") -> BaseProvider:
        """
        Resolves provider from registry. If not initialized, builds it dynamically.
        """
        pname = provider_name.strip().lower()
        
        # Build registry entries on first request
        try:
            return provider_registry.get(pname)
        except ValueError:
            # Registry miss - build dynamically
            if pname == "gemini":
                # Default model mapping
                target_model = model_name or "gemini-1.5-pro"
                provider = GeminiProvider(
                    api_key=settings.GEMINI_API_KEY,
                    model_name=target_model
                )
                provider_registry.register(pname, provider)
                return provider
            else:
                raise ValueError(f"LLM Provider factory does not support configuration for: '{provider_name}'")
