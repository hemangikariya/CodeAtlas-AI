from sqlalchemy import Column, String, Text, Integer, JSON, UUID, ForeignKey
from backend.app.adapters.database.base import Base
import uuid

class CodeChunkModel(Base):
    __tablename__ = "code_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # "MODULE", "CLASS", "FUNCTION", "METHOD", etc.
    content = Column(Text, nullable=False)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    metadata_json = Column(JSON, nullable=True)
