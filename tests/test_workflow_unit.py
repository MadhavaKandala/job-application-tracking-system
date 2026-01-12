import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.workflow_service import change_application_stage
from app.models import Application, ApplicationStage, User, Job
from fastapi import HTTPException

@pytest.mark.asyncio
async def test_valid_transition():
    db = AsyncMock()
    app = Application(id="1", stage=ApplicationStage.APPLIED, job=Job(title="Test Job"), candidate=User(email="c@c.com"))
    user = User(id="2", role="recruiter")
    
    # Applied -> Screening
    new_app = await change_application_stage(db, app, ApplicationStage.SCREENING, user)
    assert new_app.stage == ApplicationStage.SCREENING
    # Verify DB add history
    assert db.add.called
    assert db.commit.called

@pytest.mark.asyncio
async def test_invalid_transition():
    db = AsyncMock()
    app = Application(id="1", stage=ApplicationStage.APPLIED)
    user = User(id="2", role="recruiter")
    
    # Applied -> Offer (Invalid)
    with pytest.raises(HTTPException) as exc:
        await change_application_stage(db, app, ApplicationStage.OFFER, user)
    assert exc.value.status_code == 400

@pytest.mark.asyncio
async def test_rejection_transition():
    db = AsyncMock()
    app = Application(id="1", stage=ApplicationStage.SCREENING, job=Job(title="Job"), candidate=User(email="c@c.com"))
    user = User(id="2")
    
    # Screening -> Rejected (Valid)
    new_app = await change_application_stage(db, app, ApplicationStage.REJECTED, user)
    assert new_app.stage == ApplicationStage.REJECTED
