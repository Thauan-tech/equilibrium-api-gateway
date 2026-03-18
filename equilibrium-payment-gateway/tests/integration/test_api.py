import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.core.database import get_db, Base

# Banco de dados em memória para testes
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ─── Health ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# ─── Members ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_member(client):
    payload = {
        "name": "João Silva",
        "email": "joao@academia.com",
        "cpf": "12345678909",
        "password": "senha123",
    }
    response = await client.post("/api/v1/members/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["status"] == "active"
    assert "password" not in data


@pytest.mark.asyncio
async def test_create_member_duplicate_email(client):
    payload = {
        "name": "João Silva",
        "email": "joao@academia.com",
        "cpf": "12345678909",
        "password": "senha123",
    }
    await client.post("/api/v1/members/", json=payload)
    response = await client.post("/api/v1/members/", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_member_invalid_cpf(client):
    payload = {
        "name": "João Silva",
        "email": "joao@academia.com",
        "cpf": "123",  # inválido
        "password": "senha123",
    }
    response = await client.post("/api/v1/members/", json=payload)
    assert response.status_code == 422


# ─── Auth ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(client):
    # Cria membro
    await client.post("/api/v1/members/", json={
        "name": "Maria Souza",
        "email": "maria@academia.com",
        "cpf": "98765432100",
        "password": "minhasenha",
    })
    # Faz login
    response = await client.post("/api/v1/auth/login", json={
        "email": "maria@academia.com",
        "password": "minhasenha",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/v1/members/", json={
        "name": "Maria Souza",
        "email": "maria@academia.com",
        "cpf": "98765432100",
        "password": "minhasenha",
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "maria@academia.com",
        "password": "senhaerrada",
    })
    assert response.status_code == 401


# ─── Plans ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_plans_public(client):
    response = await client.get("/api/v1/plans/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_member_me_requires_auth(client):
    response = await client.get("/api/v1/members/me")
    assert response.status_code == 403  # sem token
