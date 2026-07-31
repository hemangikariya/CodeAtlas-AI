import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dev@codeatlas.ai",
            "password": "strongpassword123",
            "role": "DEVELOPER"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "dev@codeatlas.ai"
    assert data["role"] == "DEVELOPER"
    assert "id" in data
    assert data["is_active"] is True

@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dup@codeatlas.ai",
            "password": "password123",
            "role": "DEVELOPER"
        }
    )
    
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dup@codeatlas.ai",
            "password": "password456",
            "role": "DEVELOPER"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "The user with this email already exists in the system."

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    email = "login@codeatlas.ai"
    password = "secretpassword"
    
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "role": "DEVELOPER"
        }
    )
    
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": password
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "wrong@codeatlas.ai",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"

@pytest.mark.asyncio
async def test_get_current_user_me(client: AsyncClient):
    email = "me@codeatlas.ai"
    password = "mypassword"
    
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "role": "DEVELOPER"
        }
    )
    
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    token = login_resp.json()["access_token"]
    
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == email
