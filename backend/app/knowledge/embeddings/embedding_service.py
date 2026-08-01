from typing import List, Dict, Any
from backend.app.knowledge.embeddings.embedding_factory import EmbeddingFactory

class EmbeddingService:
    def __init__(self, provider_name: str = "sentence-transformers", use_mock: bool = None):
        self.provider = EmbeddingFactory.get_provider(provider_name, use_mock)

    def get_dimension(self) -> int:
        return self.provider.get_dimension()

    def get_provider_name(self) -> str:
        return self.provider.get_provider_name()

    def get_version(self) -> str:
        return self.provider.get_version()

    def embed_query(self, text: str) -> List[float]:
        return self.provider.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.provider.embed_documents(texts)
