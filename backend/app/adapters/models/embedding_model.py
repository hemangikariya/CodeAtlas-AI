from sqlalchemy import Column, String, Integer, DateTime, UUID, ForeignKey, Text
from sqlalchemy.types import TypeDecorator
from datetime import datetime
import json
import uuid

from backend.app.adapters.database.base import Base

class SafeVector(TypeDecorator):
    """
    SQLAlchemy Custom Type that uses pgvector.VECTOR in PostgreSQL
    and falls back to JSON-serialized TEXT in SQLite.
    """
    impl = Text
    cache_ok = True
    
    def __init__(self, dim: int = 384):
        super().__init__()
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            try:
                from pgvector.sqlalchemy import VECTOR
                return dialect.type_descriptor(VECTOR(self.dim))
            except ImportError:
                pass
        return dialect.type_descriptor(Text)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        # For SQLite fallback, serialize to JSON string
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        # For SQLite fallback, deserialize JSON string
        return json.loads(value)

class EmbeddingModel(Base):
    __tablename__ = "embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("code_chunks.id", ondelete="CASCADE"), nullable=False, index=True)
    vector = Column(SafeVector(384), nullable=False)
    embedding_dimension = Column(Integer, default=384, nullable=False)
    embedding_version = Column(String(50), default="v1", nullable=False)
    provider = Column(String(100), default="sentence-transformers", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
