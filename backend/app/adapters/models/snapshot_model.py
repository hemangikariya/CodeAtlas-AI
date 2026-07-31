from sqlalchemy import Column, String, DateTime, UUID, ForeignKey
from datetime import datetime
from backend.app.adapters.database.base import Base
import uuid

class SnapshotModel(Base):
    __tablename__ = "repository_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    branch = Column(String(255), nullable=True)
    commit_sha = Column(String(100), nullable=True)
    version = Column(String(50), default="v1", nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)
    upload_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
