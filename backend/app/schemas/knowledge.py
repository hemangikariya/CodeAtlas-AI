from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class SearchRequest(BaseModel):
    query: str = Field(..., description="The query string to search for.")
    search_type: str = Field("ALL", description="The search intent routing category: ALL, FUNCTION, CLASS, API, DEPENDENCY, DOCUMENTATION.")
    top_k: int = Field(5, ge=1, le=50, description="The maximum number of matches to retrieve.")
    token_limit: int = Field(4000, ge=500, le=16000, description="The maximum token budget for Context Builder prompt generation.")

class ChunkResponse(BaseModel):
    id: str
    file_id: str
    name: str
    type: str
    content: str
    start_line: int
    end_line: int
    file_path: str

class GraphContextResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

class SearchResponse(BaseModel):
    query: str
    retrieved_chunks: List[ChunkResponse]
    related_nodes: List[str]
    graph_context: GraphContextResponse
    metadata: Dict[str, Any]
    final_context: str

class GraphStatsResponse(BaseModel):
    total_nodes: int
    total_edges: int
    average_degree: float
    connected_components: int

class GraphNodeDetailResponse(BaseModel):
    id: str
    snapshot_id: str
    entity_id: Optional[str] = None
    name: str
    type: str
    properties: Dict[str, Any]

class EmbeddingDetailResponse(BaseModel):
    id: str
    chunk_id: str
    embedding_dimension: int
    embedding_version: str
    provider: str
    created_at: str
