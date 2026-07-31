from sqlalchemy import Column, String, Text, DateTime, UUID, ForeignKey
from datetime import datetime
from backend.app.adapters.database.base import Base
import uuid

class FileModel(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    path = Column(String(1024), nullable=False)
    content_chunk = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
