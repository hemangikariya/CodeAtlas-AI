from abc import ABC, abstractmethod
from typing import List

class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding vector for a single text query.
        """
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for a list of document strings.
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """
        Return the embedding dimension of the provider.
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Return the provider name.
        """
        pass

    @abstractmethod
    def get_version(self) -> str:
        """
        Return the model version string.
        """
        pass
