import uuid
from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from backend.app.knowledge.vector_store.base_vector_store import BaseVectorStore
from backend.app.adapters.models.embedding_model import EmbeddingModel
from backend.app.adapters.models.code_chunk_model import CodeChunkModel
from backend.app.adapters.models.file_model import FileModel

class PgVectorStore(BaseVectorStore):
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
                vector=vec,
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
        
        # We query and calculate cosine similarity
        # Cosine distance operator is represented by: EmbeddingModel.vector.cosine_distance(query_vector)
        # Cosine similarity = 1 - Cosine distance
        stmt = (
            select(
                EmbeddingModel.chunk_id,
                (1.0 - EmbeddingModel.vector.cosine_distance(query_vector)).label("similarity")
            )
            .join(CodeChunkModel, CodeChunkModel.id == EmbeddingModel.chunk_id)
            .join(FileModel, FileModel.id == CodeChunkModel.file_id)
            .filter(FileModel.snapshot_id == sid)
            .order_by("similarity") # Wait, pgvector order by distance is ascending, so order_by(EmbeddingModel.vector.cosine_distance(query_vector)) is correct, returning closest first!
        )
        
        # Let's order by distance ascending (closest first)
        stmt = stmt.order_by(EmbeddingModel.vector.cosine_distance(query_vector)).limit(top_k)
        
        result = await self.db.execute(stmt)
        rows = result.all()
        return [(str(row.chunk_id), float(row.similarity)) for row in rows]
