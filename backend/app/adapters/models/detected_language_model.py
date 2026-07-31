from sqlalchemy import Column, String, Integer, Float, UUID, ForeignKey
from backend.app.adapters.database.base import Base
import uuid

class DetectedLanguageModel(Base):
    __tablename__ = "detected_languages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    language = Column(String(100), nullable=False)
    file_count = Column(Integer, nullable=False)
    line_count = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)
