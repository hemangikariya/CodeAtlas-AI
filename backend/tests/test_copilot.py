import pytest
import uuid
import base64
import json
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# DB and Models
from backend.app.adapters.models.generated_artifact_model import GeneratedArtifactModel
from backend.app.adapters.models.repository_model import RepositoryModel
from backend.app.adapters.models.snapshot_model import SnapshotModel
from backend.app.adapters.models.project_model import ProjectModel

# Copilot components
from backend.app.copilot.base_generator import BaseGenerator
from backend.app.copilot.generator_registry import generator_registry
from backend.app.copilot.engineering_copilot import EngineeringCopilot
from backend.app.gateway.ai_gateway import AIGateway
from backend.app.knowledge.knowledge_service import KnowledgeService

# Exporters
from backend.app.export import MarkdownExporter, HTMLExporter, PDFExporter, JSONExporter


@pytest.mark.asyncio
async def test_generator_registry_lifecycle():
    """
    Verifies that all copilot generators are properly registered, retrievable,
    and raise appropriate errors for missing generators.
    """
    gateway = AIGateway()
    # Instantiating copilot registers all 12 default generators
    copilot = EngineeringCopilot(gateway)

    # Check registered generators list
    types = generator_registry.list_registered_types()
    assert len(types) >= 12
    assert "adr_generator" in types
    assert "repository_explainer" in types

    # Resolve existing generator
    g = generator_registry.get("adr_generator")
    assert g.name == "ADRGenerator"

    # Handle missing generator gracefully
    with pytest.raises(ValueError, match="No copilot generator found"):
        generator_registry.get("non_existent_artifact_type")


@pytest.mark.asyncio
async def test_artifact_export_layers():
    """
    Verifies that Markdown, HTML, PDF, and JSON exporters output formatted data.
    """
    mock_artifact = {
        "title": "Database Optimization Guide",
        "summary": "Guide for implementing postgres hybrid vector indices.",
        "sections": [
            {"heading": "Introduction", "content": "This covers context."},
            {"heading": "Decision", "content": "Adopt HNSW index."}
        ],
        "references": ["003_knowledge_layer.py"],
        "generator": "RepositoryExplainer",
        "generator_version": "1.0",
        "prompt_version": "1.0",
        "knowledge_snapshot": "snap-uuid-123",
        "artifact_version": "1.0",
        "created_at": "2026-08-03T12:00:00Z"
    }

    # 1. Markdown Exporter
    md = MarkdownExporter.export(mock_artifact)
    assert "# Database Optimization Guide" in md
    assert "Adopt HNSW index" in md
    assert "snap-uuid-123" in md

    # 2. HTML Exporter
    html = HTMLExporter.export(mock_artifact)
    assert "<!DOCTYPE html>" in html
    assert "<h1>Database Optimization Guide</h1>" in html
    assert "<blockquote>" in html or "<p>" in html

    # 3. PDF Exporter
    pdf_bytes = PDFExporter.export(mock_artifact)
    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert b"%%EOF" in pdf_bytes

    # 4. JSON Exporter
    js = JSONExporter.export(mock_artifact)
    data = json.loads(js)
    assert data["title"] == "Database Optimization Guide"


@pytest.mark.asyncio
async def test_every_copilot_generator(db_session: AsyncSession):
    """
    Verifies that all 12 copilot generators run successfully and write history items.
    """
    gateway = AIGateway()
    copilot = EngineeringCopilot(gateway)
    service = KnowledgeService(db_session)

    # 1. Setup mock project, repo and snapshot records
    proj_id = uuid.uuid4()
    repo_id = uuid.uuid4()
    snap_id = uuid.uuid4()

    project = ProjectModel(id=proj_id, name="TestProject", description="Desc")
    repo = RepositoryModel(id=repo_id, project_id=proj_id, name="TestRepo", url="http://github.com/mock/repo")
    snap = SnapshotModel(id=snap_id, repository_id=repo_id, version="v1", status="COMPLETED")
    
    db_session.add(project)
    db_session.add(repo)
    db_session.add(snap)
    await db_session.commit()

    # Define all 12 artifact types to test
    artifact_types = [
        "repository_explainer",
        "architecture_generator",
        "adr_generator",
        "api_designer",
        "documentation_generator",
        "test_plan_generator",
        "refactoring_advisor",
        "code_review_assistant",
        "sprint_planner",
        "implementation_planner",
        "onboarding_generator",
        "dependency_analyzer"
    ]

    for type_name in artifact_types:
        artifact = await copilot.generate_artifact(
            db=db_session,
            artifact_type=type_name,
            query="Analyze evaluation systems",
            snapshot_id=str(snap_id),
            repository_id=str(repo_id)
        )
        assert artifact["title"] is not None
        assert len(artifact["sections"]) > 0
        assert artifact["generator"] is not None


@pytest.mark.asyncio
async def test_copilot_rest_api_integration(client: AsyncClient, db_session: AsyncSession):
    """
    Verifies FastAPI endpoints and historical CRUD routes.
    """
    # 1. Authenticate Developer user
    register_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "copilot-dev@codeatlas.ai", "password": "securepass123", "role": "DEVELOPER"}
    )
    assert register_resp.status_code == 200

    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "copilot-dev@codeatlas.ai", "password": "securepass123"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Setup mock models
    proj_id = uuid.uuid4()
    repo_id = uuid.uuid4()
    snap_id = uuid.uuid4()
    project = ProjectModel(id=proj_id, name="APIProject", description="API project")
    repo = RepositoryModel(id=repo_id, project_id=proj_id, name="APIRepo", url="http://github.com/mock/api-repo")
    snap = SnapshotModel(id=snap_id, repository_id=repo_id, version="v1", status="COMPLETED")
    
    db_session.add(project)
    db_session.add(repo)
    db_session.add(snap)
    await db_session.commit()

    # 3. Test post endpoints
    endpoints = [
        ("repository", "explainer report"),
        ("architecture", "structural layout review"),
        ("adr", "pgvector choices"),
        ("api-design", "rest routes layout"),
        ("documentation", "development guides"),
        ("test-plan", "integration cases"),
        ("refactor", "solid improvements"),
        ("code-review", "pr review feedback"),
        ("sprint", "task estimations"),
        ("implementation-plan", "phases deliverables"),
        ("onboarding", "onboarding setup guides"),
        ("dependency-analysis", "circular references")
    ]

    artifact_ids = []

    for route, query in endpoints:
        resp = await client.post(
            f"/api/v1/copilot/{route}",
            json={
                "repository_id": str(repo_id),
                "snapshot_id": str(snap_id),
                "query": query,
                "export_format": "markdown"
            },
            headers=headers
        )
        assert resp.status_code == 200, f"Endpoint {route} failed: {resp.text}"
        data = resp.json()
        assert data["title"] is not None
        assert "TITLE:" in data["exported_content"] or "#" in data["exported_content"]
        artifact_ids.append(data["id"])

    # 4. Test GET historical list
    list_resp = await client.get("/api/v1/copilot/artifacts", headers=headers)
    assert list_resp.status_code == 200
    artifacts_list = list_resp.json()
    assert len(artifacts_list) >= len(endpoints)

    # 5. Test GET details
    target_id = artifact_ids[0]
    detail_resp = await client.get(
        f"/api/v1/copilot/artifacts/{target_id}",
        params={"export_format": "html"},
        headers=headers
    )
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert "html" in detail_data["exported_content"]

    # 6. Test DELETE details
    del_resp = await client.delete(f"/api/v1/copilot/artifacts/{target_id}", headers=headers)
    assert del_resp.status_code == 204

    # Verify deleted
    verify_resp = await client.get(f"/api/v1/copilot/artifacts/{target_id}", headers=headers)
    assert verify_resp.status_code == 404
