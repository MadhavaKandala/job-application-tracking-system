import pytest
import asyncio
from httpx import AsyncClient
from uuid import uuid4
from app.models import UserRole, ApplicationStage

@pytest.mark.asyncio
async def test_full_ats_flow(client: AsyncClient):
    # 1. Create Company
    company_name = f"TechCorp_{uuid4()}"
    resp = await client.post("/api/companies", json={"name": company_name})
    assert resp.status_code == 200
    company_id = resp.json()["id"]

    # 2. Register Recruiter
    recruiter_email = f"recruiter_{uuid4()}@example.com"
    resp = await client.post("/auth/register", json={
        "email": recruiter_email,
        "password": "password",
        "role": "recruiter",
        "company_id": company_id
    })
    assert resp.status_code == 200
    recruiter_token = (await client.post("/auth/login", data={"username": recruiter_email, "password": "password"})).json()["access_token"]
    recruiter_headers = {"Authorization": f"Bearer {recruiter_token}"}

    # 3. Register Candidate
    candidate_email = f"candidate_{uuid4()}@example.com"
    resp = await client.post("/auth/register", json={
        "email": candidate_email,
        "password": "password",
        "role": "candidate"
    })
    assert resp.status_code == 200
    candidate_token = (await client.post("/auth/login", data={"username": candidate_email, "password": "password"})).json()["access_token"]
    candidate_headers = {"Authorization": f"Bearer {candidate_token}"}

    # 4. Recruiter Creates Job
    job_payload = {
        "title": "Backend Engineer",
        "description": "Python expert",
        "status": "open"
    }
    resp = await client.post("/api/jobs/", json=job_payload, headers=recruiter_headers)
    assert resp.status_code == 200
    job_id = resp.json()["id"]

    # 5. Candidate Applies
    resp = await client.post(f"/api/jobs/{job_id}/applications", headers=candidate_headers)
    assert resp.status_code == 200
    app_id = resp.json()["id"]
    assert resp.json()["stage"] == "Applied"

    # 6. Recruiter Views Applications
    resp = await client.get(f"/api/jobs/{job_id}/applications", headers=recruiter_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["candidate_id"] # Should adhere to schema

    # 7. Recruiter Advances Stage (Applied -> Screening)
    resp = await client.patch(
        f"/api/applications/{app_id}/stage", 
        json={"new_stage": "Screening"},
        headers=recruiter_headers
    )
    assert resp.status_code == 200
    assert resp.json()["stage"] == "Screening"

    # 8. Verify History
    resp = await client.get(f"/api/applications/{app_id}", headers=recruiter_headers)
    assert resp.status_code == 200
    detail = resp.json()
    assert len(detail["history"]) >= 1
    assert detail["history"][0]["new_stage"] == "Screening"
    assert detail["history"][0]["old_stage"] == "Applied"

    # 9. Invalid Transition Check (Screening -> Hired [Skip])
    # Valid: Screening -> Interview. Screening -> Rejected.
    # Invalid: Screening -> Offer? Need to check state map.
    # Map: Screening -> [Interview, Rejected].
    # So Screening -> Offer should fail.
    resp = await client.patch(
        f"/api/applications/{app_id}/stage", 
        json={"new_stage": "Offer"},
        headers=recruiter_headers
    )
    assert resp.status_code == 400
