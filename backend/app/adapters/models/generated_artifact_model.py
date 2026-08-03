from sqlalchemy import Column, String, DateTime, UUID, ForeignKey, JSON
from datetime import datetime
from backend.app.adapters.database.base import Base
import uuid


class GeneratedArtifactModel(Base):
    __tablename__ = "generated_artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    artifact_type = Column(String(100), nullable=False, index=True)
    generator = Column(String(100), nullable=False)
    artifact_version = Column(String(50), default="1.0", nullable=False)
    prompt_version = Column(String(50), default="1.0", nullable=False)
    llm_provider = Column(String(100), nullable=False)
    model_name = Column(String(100), nullable=False)
    content = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
