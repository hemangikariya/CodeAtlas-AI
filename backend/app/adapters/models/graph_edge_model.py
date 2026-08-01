from sqlalchemy import Column, String, JSON, UUID, ForeignKey
from backend.app.adapters.database.base import Base
import uuid

class GraphEdgeModel(Base):
    __tablename__ = "graph_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    source_node_id = Column(UUID(as_uuid=True), ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    target_node_id = Column(UUID(as_uuid=True), ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False) # e.g. "IMPORTS", "CALLS", "DEFINES", etc.
    properties = Column(JSON, default=dict, nullable=False)
