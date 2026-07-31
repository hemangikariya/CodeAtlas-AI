from sqlalchemy import Column, String, UUID, ForeignKey
from backend.app.adapters.database.base import Base
import uuid

class FolderModel(Base):
    __tablename__ = "folders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(255), nullable=False)
    path = Column(String(1024), nullable=False)
