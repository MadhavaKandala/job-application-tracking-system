from datetime import datetime, timezone
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Application, ApplicationHistory, ApplicationStage, User
from app.services.email_tasks import send_stage_changed_email

VALID_TRANSITIONS = {
    ApplicationStage.APPLIED: [ApplicationStage.SCREENING, ApplicationStage.REJECTED],
    ApplicationStage.SCREENING: [ApplicationStage.INTERVIEW, ApplicationStage.REJECTED],
    ApplicationStage.INTERVIEW: [ApplicationStage.OFFER, ApplicationStage.REJECTED],
    ApplicationStage.OFFER: [ApplicationStage.HIRED, ApplicationStage.REJECTED],
    ApplicationStage.HIRED: [], # Terminal
    ApplicationStage.REJECTED: [], # Terminal
}

async def change_application_stage(db: AsyncSession, application: Application, new_stage: ApplicationStage, user: User):
    current_stage = application.stage
    
    # 1. Validate Transition
    # Allow idempotent updates (same stage)
    if current_stage == new_stage:
        return application

    allowed = VALID_TRANSITIONS.get(current_stage, [])
    if new_stage not in allowed:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid transition from {current_stage} to {new_stage}"
        )

    # 2. Update Application
    application.stage = new_stage
    
    # 3. Create History
    history = ApplicationHistory(
        application_id=application.id,
        old_stage=current_stage,
        new_stage=new_stage,
        changed_by=user.id,
        changed_at=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db.add(history)
    
    # 4. Commit (Transaction managed by caller or auto-commit if verified here - usually better to flush/commit here for the logic unit)
    try:
        await db.commit()
        await db.refresh(application)
    except Exception as e:
        await db.rollback()
        raise e

    # 5. Trigger Async Notification
    # We need to fetch job info for email, relying on eager load or simple fetch
    # Ideally should be efficiently loaded. For now, assuming relationships work or we fetch it.
    # Note: application.job might not be loaded. 
    # Let's re-fetch or assume caller handles reload, or just fetch title if needed.
    # Simplified: Trigger task with IDs, let task fetch? No, pass strings.
    
    # Check if we have the job and candidate loaded
    if application.job and application.candidate:
        send_stage_changed_email.delay(application.candidate.email, application.job.title, new_stage.value)
    
    return application
