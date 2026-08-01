import hashlib
import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.adapters.models.retrieval_cache_model import RetrievalCacheModel

class RetrievalCache:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _compute_hash(self, text: str) -> str:
        return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()

    async def get(self, snapshot_id: str, query: str) -> Optional[Dict[str, Any]]:
        sid = uuid.UUID(snapshot_id)
        q_hash = self._compute_hash(query)
        
        stmt = (
            select(RetrievalCacheModel)
            .filter(
                RetrievalCacheModel.snapshot_id == sid,
                RetrievalCacheModel.query_hash == q_hash,
                RetrievalCacheModel.ttl > datetime.utcnow()
            )
        )
        result = await self.db.execute(stmt)
        cache_row = result.scalars().first()
        
        if cache_row:
            return {
                "retrieved_node_ids": cache_row.retrieved_node_ids,
                "context": cache_row.context
            }
        return None

    async def set(
        self,
        snapshot_id: str,
        query: str,
        embedding_vector: List[float],
        retrieved_node_ids: List[str],
        context: str,
        expire_minutes: int = 60
    ) -> None:
        sid = uuid.UUID(snapshot_id)
        q_hash = self._compute_hash(query)
        
        # Compute embedding hash
        vec_bytes = json.dumps(embedding_vector).encode("utf-8")
        emb_hash = hashlib.sha256(vec_bytes).hexdigest()
        
        ttl_time = datetime.utcnow() + timedelta(minutes=expire_minutes)
        
        # Clear any existing cache for this exact query on this snapshot
        existing_stmt = select(RetrievalCacheModel).filter(
            RetrievalCacheModel.snapshot_id == sid,
            RetrievalCacheModel.query_hash == q_hash
        )
        existing = await self.db.execute(existing_stmt)
        for old in existing.scalars().all():
            await self.db.delete(old)
            
        new_cache = RetrievalCacheModel(
            id=uuid.uuid4(),
            query_hash=q_hash,
            embedding_hash=emb_hash,
            snapshot_id=sid,
            retrieved_node_ids=retrieved_node_ids,
            context=context,
            ttl=ttl_time
        )
        self.db.add(new_cache)
        await self.db.flush()
