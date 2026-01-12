import pytest
from httpx import AsyncClient
from uuid import uuid4
from app.models import UserRole, ApplicationStage
from app.schemas import UserCreate

# Helpers
async def create_user(client, email, role, company_id=None):
    resp = await client.post("/auth/register", json={
        "email": email,
        "password": "password",
        "role": role,
        "company_id": str(company_id) if company_id else None
    })
    return resp

async def get_token(client, email):
    resp = await client.post("/auth/login", data={"username": email, "password": "password"})
    return resp.json()["access_token"]

@pytest.mark.asyncio
async def test_auth_flow(client: AsyncClient):
    # Register
    email = f"test_{uuid4()}@example.com"
    resp = await create_user(client, email, UserRole.CANDIDATE)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == email
    assert "id" in data

    # Login
    resp = await client.post("/auth/login", data={"username": email, "password": "password"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

@pytest.mark.asyncio
async def test_job_application_workflow(client: AsyncClient):
    # 1. Setup Company & Users
    company_id = str(uuid4()) # In real DB we need to insert Company first? 
    # Yes, FK constraint. But our current auth registration doesn't insert Company, it just takes ID.
    # We must insert a company manually or via an endpoint? 
    # There is no Create Company endpoint in the requirements (Recruiter creates jobs).
    # Wait, the models have Company table. User has company_id. Job has company_id.
    # How is a company created? "Company: A company that posts jobs."
    # Missing endpoint? Requirements say "Jobs: Full CRUD... Only users with recruiter role...".
    # User Reg: "company_id (FK)". 
    # Use a fixture to insert a company directly to DB for test.
    from app.models import Company
    from app.database import AsyncSessionLocal
    
    # We'll rely on a manual insert or a raw functionality if client doesn't support it.
    # Actually, let's just insert one using the session.
    # But wait, create_user calls API.
    # Let's add a company fixture? No, just do it in the test.
    pass 
    # Will implement the test logic fully in next file write after handling company creation.
