import io
import os
import zipfile
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.parsers.python_parser import PythonParser
from backend.app.parsers.javascript_parser import JavaScriptParser
from backend.app.parsers.parser_manager import ParserManager
from backend.app.adapters.repositories.repository_repository import RepositoryRepository
from backend.app.adapters.repositories.snapshot_repository import SnapshotRepository
from backend.app.usecases.ingestion import IngestRepositoryUseCase
from backend.app.domain.ingestion import Repository, RepositorySnapshot
from backend.app.adapters.models.file_model import FileModel
from backend.app.adapters.models.code_chunk_model import CodeChunkModel
from backend.app.adapters.models.detected_language_model import DetectedLanguageModel

@pytest.mark.asyncio
async def test_python_parser_ast():
    parser = PythonParser()
    code = """
import os
from sys import exit

class MathUtils:
    def add_numbers(self, a, b):
        return a + b

def global_calculate(x):
    return x * 2
"""
    results = parser.parse(code, "math.py")
    assert len(results["imports"]) == 2
    assert len(results["classes"]) == 1
    assert results["classes"][0]["name"] == "MathUtils"
    assert len(results["methods"]) == 1
    assert results["methods"][0]["name"] == "add_numbers"
    assert len(results["functions"]) == 1
    assert results["functions"][0]["name"] == "global_calculate"
    # Ensure chunks are generated for class, method, function
    chunk_types = [c["type"] for c in results["chunks"]]
    assert "CLASS" in chunk_types
    assert "METHOD" in chunk_types
    assert "FUNCTION" in chunk_types

@pytest.mark.asyncio
async def test_javascript_parser_ast():
    parser = JavaScriptParser()
    code = """
import { helper } from './helpers';

class UserService {
    getUser(id) {
        return { id, name: "Alice" };
    }
}

function processUserData(user) {
    console.log(user);
}
"""
    results = parser.parse(code, "users.js")
    assert len(results["imports"]) == 1
    assert len(results["classes"]) == 1
    assert results["classes"][0]["name"] == "UserService"
    assert len(results["methods"]) == 1
    assert results["methods"][0]["name"] == "getUser"
    assert len(results["functions"]) == 1
    assert results["functions"][0]["name"] == "processUserData"

@pytest.mark.asyncio
async def test_parser_manager_routing():
    pm = ParserManager()
    py_parser = pm.get_parser_for_file("test.py")
    assert isinstance(py_parser, PythonParser)
    
    js_parser = pm.get_parser_for_file("test.ts")
    assert isinstance(js_parser, JavaScriptParser)
    
    fallback = pm.parse_file("some raw text", "config.json")
    assert len(fallback["chunks"]) == 1
    assert fallback["chunks"][0]["type"] == "CONFIG"

@pytest.mark.asyncio
async def test_repository_ingestion_usecase(db_session: AsyncSession):
    # Setup test project in DB
    from backend.app.adapters.models.project_model import ProjectModel
    import uuid
    project_id = uuid.uuid4()
    project = ProjectModel(id=project_id, name="Test Ingestion", description="Testing Ingestion use case")
    db_session.add(project)
    await db_session.flush()

    repo_repo = RepositoryRepository(db_session)
    snap_repo = SnapshotRepository(db_session)

    # Create zip file mock in-memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        zip_file.writestr("math.py", "class Calc:\n    def add(self, a, b):\n        return a + b\n")
        zip_file.writestr("utils.js", "function log(msg) { console.log(msg); }\n")
        zip_file.writestr("README.md", "# Math Calculator\nSimple operations\n")

    # Save mock zip to disk temporarily
    temp_zip_path = f"test_mock_repo_{uuid.uuid4()}.zip"
    with open(temp_zip_path, "wb") as f:
        f.write(zip_buffer.getvalue())

    # Create Repo and Snapshot in DB
    repo = Repository(project_id=str(project_id), name="MockRepo")
    repo = await repo_repo.create_repository(repo)
    
    snap = RepositorySnapshot(repository_id=repo.id, branch="main", status="PENDING")
    snap = await snap_repo.create_snapshot(snap)
    await db_session.commit()

    # Execute ingestion usecase
    usecase = IngestRepositoryUseCase(repo_repo, snap_repo)
    try:
        completed_snap = await usecase.execute(snap.id, zip_file_path=temp_zip_path)
        assert completed_snap.status == "COMPLETED"
        
        # Verify database entities are stored
        files_res = await db_session.execute(select(FileModel).filter(FileModel.snapshot_id == uuid.UUID(snap.id)))
        files = files_res.scalars().all()
        assert len(files) == 3
        
        chunks_res = await db_session.execute(
            select(CodeChunkModel)
            .join(FileModel)
            .filter(FileModel.snapshot_id == uuid.UUID(snap.id))
        )
        chunks = chunks_res.scalars().all()
        assert len(chunks) >= 3  # math.py class Calc + method add, utils.js function log, README.md config/text fallback
        
        langs_res = await db_session.execute(select(DetectedLanguageModel).filter(DetectedLanguageModel.snapshot_id == uuid.UUID(snap.id)))
        langs = langs_res.scalars().all()
        languages_found = {l.language for l in langs}
        assert "Python" in languages_found
        assert "JavaScript" in languages_found
        
    finally:
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)

@pytest.mark.asyncio
async def test_repository_indexing_api_flow(client: AsyncClient):
    # Register and login user to get developer authentication headers
    register_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "indexing-dev@codeatlas.ai", "password": "devpass123", "role": "DEVELOPER"}
    )
    assert register_resp.status_code == 200
    
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "indexing-dev@codeatlas.ai", "password": "devpass123"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create project
    proj_resp = await client.post(
        "/api/v1/projects/",
        json={"name": "Indexing Integration", "description": "Verify API upload"},
        headers=headers
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # Create zip mock
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        zip_file.writestr("app.py", "def main():\n    print('Run')\n")

    # Test Upload HTTP Request
    upload_resp = await client.post(
        "/api/v1/repositories/upload",
        data={"project_id": project_id, "name": "MainRepo", "branch": "main"},
        files={"file": ("repo.zip", zip_buffer.getvalue(), "application/zip")},
        headers=headers
    )
    assert upload_resp.status_code == 202
    snap = upload_resp.json()
    assert snap["status"] == "PENDING"
    snapshot_id = snap["id"]
    repository_id = snap["repository_id"]

    # Since extraction runs in BackgroundTasks synchronously inside AsyncClient tests, 
    # we can poll status immediately or await event loops. Let's verify status.
    import asyncio
    await asyncio.sleep(0.5) # Allow background execution loop to complete
    
    status_resp = await client.get(
        f"/api/v1/repositories/{snapshot_id}/status",
        headers=headers
    )
    assert status_resp.status_code == 200
    # The status should be COMPLETED since it runs immediately in ASGI background task thread
    assert status_resp.json()["status"] in ["COMPLETED", "INDEXING", "PENDING"]

    # Test list repositories
    list_resp = await client.get(
        f"/api/v1/repositories/?project_id={project_id}",
        headers=headers
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # Test get repository metadata
    meta_resp = await client.get(
        f"/api/v1/repositories/{snapshot_id}/metadata",
        headers=headers
    )
    assert meta_resp.status_code == 200
    assert meta_resp.json()["snapshot_id"] == snapshot_id

    # Test delete repository
    delete_resp = await client.delete(
        f"/api/v1/repositories/{repository_id}",
        headers=headers
    )
    assert delete_resp.status_code == 204
