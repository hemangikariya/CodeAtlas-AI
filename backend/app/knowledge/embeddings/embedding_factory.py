from backend.app.core.config import settings
from backend.app.knowledge.embeddings.base_embedding_provider import BaseEmbeddingProvider
from backend.app.knowledge.embeddings.sentence_transformer_provider import SentenceTransformerProvider

class EmbeddingFactory:
    @staticmethod
    def get_provider(provider_name: str = "sentence-transformers", use_mock: bool = None) -> BaseEmbeddingProvider:
        if use_mock is None:
            # Auto-enable mock for tests to save execution cycles and offline security
            use_mock = (settings.ENVIRONMENT == "testing")

        if provider_name == "sentence-transformers":
            return SentenceTransformerProvider(use_mock=use_mock)
            
        # Return fallback default
        return SentenceTransformerProvider(use_mock=use_mock)
