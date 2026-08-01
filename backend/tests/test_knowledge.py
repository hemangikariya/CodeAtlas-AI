import pytest
import io
import zipfile
import uuid
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.knowledge.embeddings.embedding_service import EmbeddingService
from backend.app.knowledge.vector_store.sqlite_vector_store import SqliteVectorStore
from backend.app.knowledge.graph.graph_builder import GraphBuilder
from backend.app.knowledge.graph.graph_types import NodeType, EdgeType
from backend.app.knowledge.ranking import RankingEngine
from backend.app.knowledge.context_builder import ContextBuilder
from backend.app.knowledge.retrieval_cache import RetrievalCache

from backend.app.adapters.models.graph_node_model import GraphNodeModel
from backend.app.adapters.models.graph_edge_model import GraphEdgeModel
from backend.app.adapters.models.embedding_model import EmbeddingModel
from backend.app.adapters.models.retrieval_cache_model import RetrievalCacheModel

@pytest.mark.asyncio
async def test_embedding_service_mock():
    # Verify mock provider returns deterministic stable floats offline
    service = EmbeddingService(use_mock=True)
    assert service.get_dimension() == 384
    assert service.get_provider_name() == "sentence-transformers"
    
    vec1 = service.embed_query("hello world")
    vec2 = service.embed_query("hello world")
    vec3 = service.embed_query("another test")
    
    assert len(vec1) == 384
    assert vec1 == vec2
    assert vec1 != vec3
    assert all(isinstance(x, float) for x in vec1)

@pytest.mark.asyncio
async def test_ranking_engine_and_context_builder():
    chunks = [
        ({"id": "c1", "name": "my_function", "type": "FUNCTION", "content": "def my_function(): pass", "start_line": 1, "end_line": 2, "file_path": "app.py"}, 0.8),
        ({"id": "c2", "name": "MyClass", "type": "CLASS", "content": "class MyClass: pass", "start_line": 5, "end_line": 10, "file_path": "models.py"}, 0.6)
    ]
    
    # Assert query term boost
    ranked = RankingEngine.rank_chunks(chunks, query="test my_function class")
    assert len(ranked) == 2
    # c1 should get direct name match boost (+0.15) and function keyword boost (+0.08)
    # c2 should get class keyword boost (+0.10)
    assert ranked[0][0]["id"] == "c1"
    
    # Assert ContextBuilder budget limits
    context = ContextBuilder.build_context([ranked[0][0]], token_limit=50)
    assert "Symbol: my_function" in context
    assert "MyClass" not in context

@pytest.mark.asyncio
async def test_knowledge_api_and_pipeline_integration(client: AsyncClient, db_session: AsyncSession):
    # 1. Setup authenticated user
    register_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "knowledge-dev@codeatlas.ai", "password": "devpass123", "role": "DEVELOPER"}
    )
    assert register_resp.status_code == 200

    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "knowledge-dev@codeatlas.ai", "password": "devpass123"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create project
    proj_resp = await client.post(
        "/api/v1/projects/",
        json={"name": "Knowledge Test Proj", "description": "Validate vector search & graph traversal"},
        headers=headers
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # 3. Create zip mock repository
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        # File 1: Python
        zip_file.writestr(
            "math_utils.py",
            "def add_numbers(a, b):\n    return a + b\n\nclass Calculator:\n    def evaluate(self):\n        return 42\n"
        )
        # File 2: Javascript with import dependency
        zip_file.writestr(
            "app.js",
            "import { add_numbers } from './math_utils.py';\nfunction run() {\n    return add_numbers(2, 3);\n}\n"
        )

    # 4. Upload zip payload
    upload_resp = await client.post(
        "/api/v1/repositories/upload",
        data={"project_id": project_id, "name": "KnowledgeRepo", "branch": "main"},
        files={"file": ("repo.zip", zip_buffer.getvalue(), "application/zip")},
        headers=headers
    )
    assert upload_resp.status_code == 202
    snap = upload_resp.json()
    snapshot_id = snap["id"]
    repository_id = snap["repository_id"]

    # Wait for ingestion pipeline background execution
    await asyncio.sleep(1.0)

    # 5. Check if Snapshot completed successfully
    status_resp = await client.get(
        f"/api/v1/repositories/{snapshot_id}/status",
        headers=headers
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "COMPLETED"

    # Verify Knowledge Graph elements created in DB
    nodes_res = await db_session.execute(
        select(GraphNodeModel).filter(GraphNodeModel.snapshot_id == uuid.UUID(snapshot_id))
    )
    db_nodes = nodes_res.scalars().all()
    assert len(db_nodes) > 0
    node_types = {n.type for n in db_nodes}
    assert NodeType.FILE.value in node_types
    assert NodeType.FUNCTION.value in node_types
    assert NodeType.CLASS.value in node_types

    edges_res = await db_session.execute(
        select(GraphEdgeModel).filter(GraphEdgeModel.snapshot_id == uuid.UUID(snapshot_id))
    )
    db_edges = edges_res.scalars().all()
    assert len(db_edges) > 0
    edge_types = {e.type for e in db_edges}
    assert EdgeType.DEFINES.value in edge_types
    assert EdgeType.IMPORTS.value in edge_types

    # Verify Vector Embeddings created in DB
    emb_res = await db_session.execute(select(EmbeddingModel))
    db_embs = emb_res.scalars().all()
    assert len(db_embs) > 0

    # 6. Test GET statistics endpoint
    stats_resp = await client.get(
        f"/api/v1/repositories/{snapshot_id}/graph/statistics",
        headers=headers
    )
    assert stats_resp.status_code == 200
    stats_data = stats_resp.json()
    assert stats_data["total_nodes"] > 0
    assert stats_data["total_edges"] > 0
    assert stats_data["connected_components"] > 0

    # 7. Test POST search endpoint
    search_resp = await client.post(
        f"/api/v1/search?snapshot_id={snapshot_id}",
        json={"query": "evaluate sum method", "search_type": "FUNCTION", "top_k": 3},
        headers=headers
    )
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["query"] == "function method evaluate sum method"
    assert len(search_data["retrieved_chunks"]) > 0
    assert len(search_data["related_nodes"]) > 0
    assert "=== RETRIEVED REPOSITORY CONTEXT ===" in search_data["final_context"]

    # 8. Test GET context endpoint
    context_resp = await client.get(
        f"/api/v1/repositories/{snapshot_id}/context?query=calculator evaluate&token_limit=1000",
        headers=headers
    )
    assert context_resp.status_code == 200
    context_data = context_resp.json()
    assert "final_context" in context_data
    assert "Calculator" in context_data["final_context"]

    # 9. Test cache hits - retrieving a second time should hit the retrieval cache
    cached_db_res = await db_session.execute(select(RetrievalCacheModel))
    cached_rows = cached_db_res.scalars().all()
    assert len(cached_rows) > 0
