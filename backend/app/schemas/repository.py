from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

class RepositoryCreate(BaseModel):
    name: str = Field(..., max_length=255)
    url: Optional[str] = Field(None, max_length=1024)
    branch: Optional[str] = Field(None, max_length=255)

class RepositoryResponse(BaseModel):
    id: str
    project_id: str
    name: str
    url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SnapshotResponse(BaseModel):
    id: str
    repository_id: str
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    version: str
    status: str
    upload_time: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class StatisticsResponse(BaseModel):
    snapshot_id: str
    total_files: int
    total_folders: int
    total_classes: int
    total_methods: int
    total_functions: int
    total_lines_of_code: int
    total_dependencies: int
    total_languages: int

    class Config:
        from_attributes = True

class StatusResponse(BaseModel):
    snapshot_id: str
    status: str

class FolderSchema(BaseModel):
    id: str
    name: str
    path: str
    parent_folder_id: Optional[str] = None

class FileSchema(BaseModel):
    id: str
    name: str
    path: str
    folder_id: Optional[str] = None

class CodeChunkSchema(BaseModel):
    id: str
    file_id: str
    name: str
    type: str
    content: str
    start_line: int
    end_line: int
    metadata_json: Optional[Dict[str, Any]] = None

class DependencySchema(BaseModel):
    id: str
    source: str
    target: str
    type: str

class DetectedLanguageSchema(BaseModel):
    id: str
    language: str
    file_count: int
    line_count: int
    percentage: float

class MetadataResponse(BaseModel):
    snapshot_id: str
    folders: List[FolderSchema] = []
    files: List[FileSchema] = []
    chunks: List[CodeChunkSchema] = []
    dependencies: List[DependencySchema] = []
    languages: List[DetectedLanguageSchema] = []
