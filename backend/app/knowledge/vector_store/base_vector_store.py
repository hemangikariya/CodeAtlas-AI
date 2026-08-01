from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

class BaseVectorStore(ABC):
    @abstractmethod
    async def add_embeddings(
        self,
        chunk_ids: List[str],
        vectors: List[List[float]],
        provider: str,
        version: str
    ) -> None:
        """
        Store multiple vector embeddings for code chunks in the database.
        """
        pass

    @abstractmethod
    async def similarity_search(
        self,
        snapshot_id: str,
        query_vector: List[float],
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Perform cosine similarity search on vector embeddings for a specific snapshot.
        Returns a list of Tuples (chunk_id, similarity_score).
        """
        pass
