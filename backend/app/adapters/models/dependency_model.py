from sqlalchemy import Column, String, UUID, ForeignKey
from backend.app.adapters.database.base import Base
import uuid

class DependencyModel(Base):
    __tablename__ = "dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(String(1024), nullable=False)
    target = Column(String(1024), nullable=False)
    type = Column(String(50), nullable=False)  # "INTERNAL", "EXTERNAL"
