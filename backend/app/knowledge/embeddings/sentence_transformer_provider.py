from typing import List
import hashlib
import random

from backend.app.knowledge.embeddings.base_embedding_provider import BaseEmbeddingProvider

class SentenceTransformerProvider(BaseEmbeddingProvider):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", use_mock: bool = False):
        self.model_name = model_name
        self.use_mock = use_mock
        self.dimension = 384
        
        self.model = None
        if not self.use_mock:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name)
            except Exception as e:
                # If loading fails (e.g. offline during initialization), fall back to mock
                self.use_mock = True

    def embed_query(self, text: str) -> List[float]:
        if self.use_mock or self.model is None:
            return self._generate_mock_vector(text)
        return self.model.encode(text).tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self.use_mock or self.model is None:
            return [self._generate_mock_vector(t) for t in texts]
        return self.model.encode(texts).tolist()

    def get_dimension(self) -> int:
        return self.dimension

    def get_provider_name(self) -> str:
        return "sentence-transformers"

    def get_version(self) -> str:
        return self.model_name

    def _generate_mock_vector(self, text: str) -> List[float]:
        # Generate stable, text-seeded deterministic floats between -1.0 and 1.0
        sha = hashlib.sha256(text.encode("utf-8")).digest()
        rng = random.Random(int.from_bytes(sha, "big"))
        return [rng.uniform(-1.0, 1.0) for _ in range(self.dimension)]
