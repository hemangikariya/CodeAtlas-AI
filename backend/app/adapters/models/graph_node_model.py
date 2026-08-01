from sqlalchemy import Column, String, JSON, UUID, ForeignKey
from backend.app.adapters.database.base import Base
import uuid

class GraphNodeModel(Base):
    __tablename__ = "graph_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True) # Optional link to AST file_id, folder_id, chunk_id
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False) # e.g., "REPOSITORY", "SNAPSHOT", "FOLDER", "FILE", "CLASS", etc.
    properties = Column(JSON, default=dict, nullable=False)
