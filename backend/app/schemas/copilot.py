from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class CopilotArtifactRequest(BaseModel):
    repository_id: str = Field(..., description="Target repository UUID identifier.")
    snapshot_id: str = Field(..., description="Target snapshot UUID identifier.")
    query: str = Field(..., description="Context instruction query for artifact creation.")
    export_format: Optional[str] = Field("json", description="Export target formats: 'json', 'markdown', 'html', 'pdf'.")


class ArtifactSection(BaseModel):
    heading: str = Field(..., description="Heading/title of this artifact section.")
    content: str = Field(..., description="Section findings body in Markdown formats.")


class CopilotArtifactResponse(BaseModel):
    id: str = Field(..., description="Generated artifact historical database UUID.")
    title: str = Field(..., description="Generated artifact title.")
    summary: str = Field(..., description="High level summary of the artifact findings.")
    sections: List[ArtifactSection] = Field(..., description="Parsed section details blocks.")
    references: List[str] = Field(..., description="Referenced files or components lists.")
    generator: str = Field(..., description="Class name of the generator driving this.")
    generator_version: str = Field(..., description="Active version of the generator class.")
    prompt_version: str = Field(..., description="Version of system prompt template used.")
    knowledge_snapshot: str = Field(..., description="Matching snapshot UUID index.")
    artifact_version: str = Field(..., description="Artifact payload schema version.")
    created_at: str = Field(..., description="Creation UTC timestamp.")
    exported_content: Optional[str] = Field(None, description="The formatted exported content (or base64 encoded string for PDF).")


class HistoricalArtifactListItem(BaseModel):
    id: str
    repository_id: str
    snapshot_id: str
    artifact_type: str
    generator: str
    artifact_version: str
    prompt_version: str
    llm_provider: str
    model_name: str
    created_at: Any

    class Config:
        from_attributes = True
