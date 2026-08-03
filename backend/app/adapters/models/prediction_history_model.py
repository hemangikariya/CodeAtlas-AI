from sqlalchemy import Column, String, Float, DateTime, UUID, ForeignKey
from datetime import datetime
from backend.app.adapters.database.base import Base
import uuid


class PredictionHistoryModel(Base):
    __tablename__ = "prediction_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    prediction_type = Column(String(100), nullable=False, index=True)  # maintainability, bug-risk, complexity, repository-health
    prediction = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    model_version = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
