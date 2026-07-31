from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

@dataclass
class Repository:
    project_id: str
    name: str
    url: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class RepositorySnapshot:
    repository_id: str
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    version: str = "v1"
    status: str = "PENDING"  # "PENDING", "UPLOADING", "EXTRACTING", "PARSING", "INDEXING", "COMPLETED", "FAILED"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    upload_time: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Folder:
    snapshot_id: str
    name: str
    path: str
    parent_folder_id: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class File:
    snapshot_id: str
    name: str
    path: str
    content_chunk: str
    folder_id: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class CodeChunk:
    file_id: str
    name: str
    type: str  # "MODULE", "CLASS", "FUNCTION", "METHOD", "INTERFACE", "ENUM", "README", "CONFIG"
    content: str
    start_line: int
    end_line: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class Dependency:
    snapshot_id: str
    source: str
    target: str
    type: str  # "INTERNAL", "EXTERNAL"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class DetectedLanguage:
    snapshot_id: str
    language: str
    file_count: int
    line_count: int
    percentage: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class RepositoryStatistics:
    snapshot_id: str
    total_files: int = 0
    total_folders: int = 0
    total_classes: int = 0
    total_methods: int = 0
    total_functions: int = 0
    total_lines_of_code: int = 0
    total_dependencies: int = 0
    total_languages: int = 0
