import uuid
import math
from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.knowledge.vector_store.base_vector_store import BaseVectorStore
from backend.app.adapters.models.embedding_model import EmbeddingModel
from backend.app.adapters.models.code_chunk_model import CodeChunkModel
from backend.app.adapters.models.file_model import FileModel

class SqliteVectorStore(BaseVectorStore):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_embeddings(
        self,
        chunk_ids: List[str],
        vectors: List[List[float]],
        provider: str,
        version: str
    ) -> None:
        for cid, vec in zip(chunk_ids, vectors):
            model = EmbeddingModel(
                id=uuid.uuid4(),
                chunk_id=uuid.UUID(cid),
                vector=vec,  # SafeVector converts to JSON string for SQLite
                embedding_dimension=len(vec),
                embedding_version=version,
                provider=provider
            )
            self.db.add(model)
        await self.db.flush()

    async def similarity_search(
        self,
        snapshot_id: str,
        query_vector: List[float],
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        sid = uuid.UUID(snapshot_id)
        
        # In SQLite, we retrieve all embeddings for this snapshot
        # and calculate cosine similarity in memory.
        stmt = (
            select(EmbeddingModel.chunk_id, EmbeddingModel.vector)
            .join(CodeChunkModel, CodeChunkModel.id == EmbeddingModel.chunk_id)
            .join(FileModel, FileModel.id == CodeChunkModel.file_id)
            .filter(FileModel.snapshot_id == sid)
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        
        scores = []
        for row in rows:
            chunk_id = str(row.chunk_id)
            db_vec = row.vector  # SafeVector deserializes JSON string back to list of floats
            if db_vec:
                score = self._cosine_similarity(query_vector, db_vec)
                scores.append((chunk_id, score))
                
        # Sort descending by score (highest similarity first)
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm_v1 = math.sqrt(sum(a * a for a in v1))
        norm_v2 = math.sqrt(sum(b * b for b in v2))
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
        return dot_product / (norm_v1 * norm_v2)
