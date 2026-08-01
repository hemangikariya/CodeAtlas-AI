from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Dict, Any, Optional

from backend.app.core.dependencies import get_db, get_current_active_developer
from backend.app.domain.models import User
from backend.app.adapters.models.graph_node_model import GraphNodeModel
from backend.app.adapters.models.graph_edge_model import GraphEdgeModel
from backend.app.adapters.models.embedding_model import EmbeddingModel
from backend.app.adapters.repositories.repository_repository import RepositoryRepository
from backend.app.adapters.repositories.snapshot_repository import SnapshotRepository

from backend.app.schemas.knowledge import (
    SearchRequest, SearchResponse, GraphStatsResponse,
    GraphNodeDetailResponse, EmbeddingDetailResponse
)
from backend.app.knowledge.semantic_search import SemanticSearch
from backend.app.knowledge.graph.graph_queries import GraphQueries
from backend.app.knowledge.graph.graph_traversal import GraphTraversal
from backend.app.knowledge.hybrid_retriever import HybridRetriever

router = APIRouter()

async def get_resolved_snapshot_id(id_str: str, db: AsyncSession) -> str:
    try:
        uid = uuid.UUID(id_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid UUID format.")
        
    repo_repo = RepositoryRepository(db)
    repo = await repo_repo.get_repository(id_str)
    if repo:
        snap_repo = SnapshotRepository(db)
        snapshots = await snap_repo.get_repository_snapshots(id_str)
        completed = [s for s in snapshots if s.status == "COMPLETED"]
        if completed:
            # Return latest completed snapshot ID
            return str(completed[-1].id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Repository has no completed indexing snapshots."
        )
        
    snap_repo = SnapshotRepository(db)
    snap = await snap_repo.get_snapshot(id_str)
    if snap:
        return id_str
        
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository or Snapshot not found.")

@router.post("/search", response_model=SearchResponse)
async def global_search(
    request: SearchRequest,
    snapshot_id: str = Query(..., description="Target snapshot or repository ID to search in."),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    resolved_id = await get_resolved_snapshot_id(snapshot_id, db)
    search_service = SemanticSearch(db)
    results = await search_service.search(
        snapshot_id=resolved_id,
        query=request.query,
        search_type=request.search_type,
        top_k=request.top_k,
        token_limit=request.token_limit
    )
    return results

@router.get("/repositories/{id}/knowledge")
async def get_repository_knowledge(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    resolved_id = await get_resolved_snapshot_id(id, db)
    queries = GraphQueries(db)
    stats = await queries.get_graph_statistics(resolved_id)
    
    # Load sample nodes & edges for a summary graph view
    traversal = GraphTraversal(db)
    res_nodes = await db.execute(
        select(GraphNodeModel.id).filter(GraphNodeModel.snapshot_id == uuid.UUID(resolved_id)).limit(10)
    )
    initial_ids = [str(n) for n in res_nodes.scalars().all()]
    nodes, edges = await traversal.expand_graph(resolved_id, initial_ids, max_depth=1)
    
    return {
        "snapshot_id": resolved_id,
        "statistics": stats,
        "summary_graph": {
            "nodes": nodes,
            "edges": edges
        }
    }

@router.get("/repositories/{id}/context")
async def get_repository_context(
    id: str,
    query: str = Query(..., description="Query for context generation."),
    token_limit: int = Query(4000, description="Max token budget."),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    resolved_id = await get_resolved_snapshot_id(id, db)
    retriever = HybridRetriever(db)
    res = await retriever.retrieve(resolved_id, query, token_limit=token_limit)
    return {
        "snapshot_id": resolved_id,
        "query": query,
        "final_context": res["final_context"]
    }

@router.get("/repositories/{id}/graph")
async def get_repository_graph(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    resolved_id = await get_resolved_snapshot_id(id, db)
    queries = GraphQueries(db)
    
    # Get all nodes and edges for this snapshot
    res_nodes = await db.execute(select(GraphNodeModel).filter(GraphNodeModel.snapshot_id == uuid.UUID(resolved_id)))
    res_edges = await db.execute(select(GraphEdgeModel).filter(GraphEdgeModel.snapshot_id == uuid.UUID(resolved_id)))
    
    nodes = [{
        "id": str(n.id),
        "name": n.name,
        "type": n.type,
        "properties": n.properties,
        "entity_id": str(n.entity_id) if n.entity_id else None
    } for n in res_nodes.scalars().all()]
    
    edges = [{
        "id": str(e.id),
        "source_node_id": str(e.source_node_id),
        "target_node_id": str(e.target_node_id),
        "type": e.type,
        "properties": e.properties
    } for e in res_edges.scalars().all()]
    
    return {
        "snapshot_id": resolved_id,
        "nodes": nodes,
        "edges": edges
    }

@router.get("/repositories/{id}/graph/statistics", response_model=GraphStatsResponse)
async def get_graph_statistics(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    resolved_id = await get_resolved_snapshot_id(id, db)
    queries = GraphQueries(db)
    stats = await queries.get_graph_statistics(resolved_id)
    return stats

@router.get("/repositories/{id}/graph/node/{node_id}", response_model=GraphNodeDetailResponse)
async def get_graph_node_details(
    id: str,
    node_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    resolved_id = await get_resolved_snapshot_id(id, db)
    try:
        nid = uuid.UUID(node_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid node UUID.")
        
    node_res = await db.execute(
        select(GraphNodeModel)
        .filter(GraphNodeModel.snapshot_id == uuid.UUID(resolved_id), GraphNodeModel.id == nid)
    )
    node = node_res.scalars().first()
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found.")
        
    return {
        "id": str(node.id),
        "snapshot_id": str(node.snapshot_id),
        "entity_id": str(node.entity_id) if node.entity_id else None,
        "name": node.name,
        "type": node.type,
        "properties": node.properties
    }

@router.get("/repositories/{id}/search", response_model=SearchResponse)
async def repository_search(
    id: str,
    query: str = Query(..., description="Search query string."),
    search_type: str = Query("ALL", description="Intent scope category."),
    top_k: int = Query(5, description="Max results."),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    resolved_id = await get_resolved_snapshot_id(id, db)
    search_service = SemanticSearch(db)
    results = await search_service.search(
        snapshot_id=resolved_id,
        query=query,
        search_type=search_type,
        top_k=top_k
    )
    return results

@router.get("/repositories/{id}/search/similar", response_model=SearchResponse)
async def find_similar_chunks(
    id: str,
    chunk_id: str = Query(..., description="Source code chunk ID to find similarities for."),
    top_k: int = Query(5, description="Max results."),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    resolved_id = await get_resolved_snapshot_id(id, db)
    # Perform similarity using target chunk's contents as query
    try:
        cid = uuid.UUID(chunk_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid chunk UUID.")
        
    # Get source chunk content
    from backend.app.adapters.models.code_chunk_model import CodeChunkModel
    chunk_res = await db.execute(select(CodeChunkModel).filter(CodeChunkModel.id == cid))
    chunk = chunk_res.scalars().first()
    if not chunk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source chunk not found.")
        
    search_service = SemanticSearch(db)
    results = await search_service.search(
        snapshot_id=resolved_id,
        query=chunk.content,
        search_type="ALL",
        top_k=top_k
    )
    return results

@router.get("/repositories/{id}/embeddings", response_model=List[EmbeddingDetailResponse])
async def get_repository_embeddings(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_developer)
):
    resolved_id = await get_resolved_snapshot_id(id, db)
    from backend.app.adapters.models.code_chunk_model import CodeChunkModel
    from backend.app.adapters.models.file_model import FileModel
    
    stmt = (
        select(EmbeddingModel)
        .join(CodeChunkModel, CodeChunkModel.id == EmbeddingModel.chunk_id)
        .join(FileModel, FileModel.id == CodeChunkModel.file_id)
        .filter(FileModel.snapshot_id == uuid.UUID(resolved_id))
    )
    result = await db.execute(stmt)
    embeddings = result.scalars().all()
    
    return [{
        "id": str(emb.id),
        "chunk_id": str(emb.chunk_id),
        "embedding_dimension": emb.embedding_dimension,
        "embedding_version": emb.embedding_version,
        "provider": emb.provider,
        "created_at": emb.created_at.isoformat()
    } for emb in embeddings]
