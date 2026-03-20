import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ─── Health ───────────────────────────────────────────────────────────────────


async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# ─── Members ──────────────────────────────────────────────────────────────────


async def test_create_member(client):
    response = await client.post(
        "/api/v1/members/",
        json={
            "name": "João Silva",
            "email": "joao@academia.com",
            "cpf": "12345678909",
            "password": "senha123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "joao@academia.com"
    assert data["status"] == "active"
    assert "password" not in data


async def test_create_member_duplicate_email(client):
    payload = {
        "name": "João Silva",
        "email": "duplicado@academia.com",
        "cpf": "12345678909",
        "password": "senha123",
    }
    await client.post("/api/v1/members/", json=payload)
    response = await client.post("/api/v1/members/", json=payload)
    assert response.status_code == 409


async def test_create_member_invalid_cpf(client):
    response = await client.post(
        "/api/v1/members/",
        json={
            "name": "João Silva",
            "email": "joao@academia.com",
            "cpf": "123",
            "password": "senha123",
        },
    )
    assert response.status_code == 422


# ─── Auth ─────────────────────────────────────────────────────────────────────


async def test_login_success(client):
    await client.post(
        "/api/v1/members/",
        json={
            "name": "Maria Souza",
            "email": "maria@academia.com",
            "cpf": "98765432100",
            "password": "minhasenha",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "maria@academia.com", "password": "minhasenha"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client):
    await client.post(
        "/api/v1/members/",
        json={
            "name": "Maria Souza",
            "email": "maria2@academia.com",
            "cpf": "98765432100",
            "password": "minhasenha",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "maria2@academia.com", "password": "senhaerrada"},
    )
    assert response.status_code == 401


# ─── Plans ────────────────────────────────────────────────────────────────────


async def test_list_plans_public(client):
    response = await client.get("/api/v1/plans/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ─── Auth guard ───────────────────────────────────────────────────────────────


async def test_get_member_me_requires_auth(client):
    response = await client.get("/api/v1/members/me")
    assert response.status_code == 403
