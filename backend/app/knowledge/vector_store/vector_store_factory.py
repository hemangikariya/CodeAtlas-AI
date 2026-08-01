from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.knowledge.vector_store.base_vector_store import BaseVectorStore
from backend.app.knowledge.vector_store.pgvector_store import PgVectorStore
from backend.app.knowledge.vector_store.sqlite_vector_store import SqliteVectorStore

class VectorStoreFactory:
    @staticmethod
    def get_vector_store(db: AsyncSession) -> BaseVectorStore:
        dialect_name = db.bind.dialect.name
        if dialect_name == "sqlite":
            return SqliteVectorStore(db)
        return PgVectorStore(db)
