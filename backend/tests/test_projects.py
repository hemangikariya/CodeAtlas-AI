import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_project_crud_lifecycle_rbac(client: AsyncClient):
    dev_email = "project-dev@codeatlas.ai"
    dev_pass = "devpass123"
    await client.post(
        "/api/v1/auth/register",
        json={"email": dev_email, "password": dev_pass, "role": "DEVELOPER"}
    )
    
    dev_login = await client.post(
        "/api/v1/auth/login",
        data={"username": dev_email, "password": dev_pass}
    )
    dev_token = dev_login.json()["access_token"]
    
    admin_email = "project-admin@codeatlas.ai"
    admin_pass = "adminpass123"
    await client.post(
        "/api/v1/auth/register",
        json={"email": admin_email, "password": admin_pass, "role": "ADMIN"}
    )
    
    admin_login = await client.post(
        "/api/v1/auth/login",
        data={"username": admin_email, "password": admin_pass}
    )
    admin_token = admin_login.json()["access_token"]

    blocked_create = await client.post(
        "/api/v1/projects/",
        json={"name": "No Auth Repo", "description": "Blocked"}
    )
    assert blocked_create.status_code == 401
    
    create_resp = await client.post(
        "/api/v1/projects/",
        json={"name": "Atlas Core", "description": "Core ingestion layer"},
        headers={"Authorization": f"Bearer {dev_token}"}
    )
    assert create_resp.status_code == 201
    project = create_resp.json()
    assert project["name"] == "Atlas Core"
    project_id = project["id"]
    
    get_resp = await client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {dev_token}"}
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Atlas Core"
    
    list_resp = await client.get(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {dev_token}"}
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1
    
    update_resp = await client.put(
        f"/api/v1/projects/{project_id}",
        json={"name": "Atlas Core Extended", "description": "Updated"},
        headers={"Authorization": f"Bearer {dev_token}"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Atlas Core Extended"
    
    delete_blocked = await client.delete(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {dev_token}"}
    )
    assert delete_blocked.status_code == 403
    
    delete_success = await client.delete(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert delete_success.status_code == 200
    
    get_deleted = await client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {dev_token}"}
    )
    assert get_deleted.status_code == 404
