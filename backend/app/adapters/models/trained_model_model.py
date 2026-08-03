from sqlalchemy import Column, String, Float, DateTime, UUID
from datetime import datetime
from backend.app.adapters.database.base import Base
import uuid


class TrainedModelModel(Base):
    __tablename__ = "trained_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    algorithm = Column(String(100), nullable=False)
    dataset = Column(String(255), nullable=True)
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1 = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
