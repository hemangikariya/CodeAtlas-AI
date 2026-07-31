from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid

@dataclass
class Event:
    event_id: str = str(uuid.uuid4())
    timestamp: datetime = datetime.utcnow()

@dataclass
class RepositoryUploadedEvent(Event):
    project_id: str = ""
    repository_id: str = ""
    snapshot_id: str = ""
    file_path: Optional[str] = None
    local_dir_path: Optional[str] = None

@dataclass
class RepositoryExtractedEvent(Event):
    snapshot_id: str = ""
    extract_path: str = ""

@dataclass
class RepositoryParsedEvent(Event):
    snapshot_id: str = ""
    files_count: int = 0

@dataclass
class MetadataExtractedEvent(Event):
    snapshot_id: str = ""
    classes_count: int = 0
    methods_count: int = 0

@dataclass
class ChunkGenerationCompletedEvent(Event):
    snapshot_id: str = ""
    chunks_count: int = 0

@dataclass
class SnapshotCompletedEvent(Event):
    snapshot_id: str = ""
    status: str = "COMPLETED"
