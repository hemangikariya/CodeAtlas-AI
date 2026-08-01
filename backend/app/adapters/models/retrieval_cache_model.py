from sqlalchemy import Column, String, Text, DateTime, JSON, UUID, ForeignKey
from backend.app.adapters.database.base import Base
from datetime import datetime
import uuid

class RetrievalCacheModel(Base):
    __tablename__ = "retrieval_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_hash = Column(String(64), nullable=False, index=True)
    embedding_hash = Column(String(64), nullable=False)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    retrieved_node_ids = Column(JSON, nullable=False, default=list)
    context = Column(Text, nullable=False)
    ttl = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
