from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models import Application, Job, User, UserRole, ApplicationStage, ApplicationHistory
from app.schemas import ApplicationResponse, ApplicationUpdateStage, ApplicationDetailResponse, ApplicationCreate
from app.deps import get_current_user, RoleChecker
from app.services.workflow_service import change_application_stage
from app.services.email_tasks import send_application_submitted_email, send_new_application_email

router = APIRouter(tags=["Applications"])

# Apply for a job
@router.post("/api/jobs/{job_id}/applications", response_model=ApplicationResponse)
async def apply_for_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.CANDIDATE]))
):
    # Check if job exists and is open
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalars().first()
    if not job or job.status != "open":
        raise HTTPException(status_code=400, detail="Job not found or not open")

    # Check if already applied
    existing_app = await db.execute(
        select(Application).where(Application.job_id == job_id, Application.candidate_id == current_user.id)
    )
    if existing_app.scalars().first():
        raise HTTPException(status_code=400, detail="Already applied for this job")

    application = Application(
        job_id=job_id,
        candidate_id=current_user.id,
        stage=ApplicationStage.APPLIED
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    
    # Send Emails Background
    # Need to get recruiter email. 
    # Recruiter is the JOB creator.
    recruiter_result = await db.execute(select(User).where(User.id == job.created_by))
    recruiter = recruiter_result.scalars().first()
    
    send_application_submitted_email.delay(current_user.email, job.title)
    if recruiter:
        send_new_application_email.delay(recruiter.email, job.title)

    return application

# Update Stage
@router.patch("/api/applications/{app_id}/stage", response_model=ApplicationResponse)
async def update_application_stage(
    app_id: UUID,
    stage_in: ApplicationUpdateStage,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.RECRUITER, UserRole.HIRING_MANAGER]))
):
    # Load application with job to check company permissions
    result = await db.execute(select(Application).options(selectinload(Application.job), selectinload(Application.candidate)).where(Application.id == app_id))
    application = result.scalars().first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
        
    # Check permission
    # Recruiter/HM checks company_id
    if application.job.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Not authorized for this application")
        
    # Workflow Service handles validation, DB update, history log, and email
    if not application.job: # Ensure job logic if selectinload fails (it shouldn't) - wait, selectinload is for async
         pass # Already used selectinload

    # We need to pass loaded objects or load them inside service? 
    # Workflow service expects application object.
    # Service also needs candidate loaded for email.
    
    # Let's ensure candidate is loaded for email
    # Re-fetch with candidate if needed, or pass it.
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.job), selectinload(Application.candidate))
        .where(Application.id == app_id)
    )
    application = result.scalars().first()

    updated_app = await change_application_stage(db, application, stage_in.new_stage, current_user)
    return updated_app

# Get Application Details
@router.get("/api/applications/{app_id}", response_model=ApplicationDetailResponse)
async def get_application(
    app_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.history), selectinload(Application.job))
        .where(Application.id == app_id)
    )
    application = result.scalars().first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Access Control
    if current_user.role == UserRole.CANDIDATE:
        if application.candidate_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role in [UserRole.RECRUITER, UserRole.HIRING_MANAGER]:
         if application.job.company_id != current_user.company_id:
             raise HTTPException(status_code=403, detail="Not authorized")
             
    return application

# List Applications for Candidate (My Applications)
@router.get("/api/me/applications", response_model=List[ApplicationResponse])
async def get_my_applications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.CANDIDATE]))
):
    result = await db.execute(
        select(Application).where(Application.candidate_id == current_user.id)
    )
    return result.scalars().all()

# List Applications for Job (Recruiter)
@router.get("/api/jobs/{job_id}/applications", response_model=List[ApplicationResponse])
async def get_job_applications(
    job_id: UUID,
    stage: Optional[ApplicationStage] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.RECRUITER, UserRole.HIRING_MANAGER]))
):
    # Check Job ownership
    job_res = await db.execute(select(Job).where(Job.id == job_id))
    job = job_res.scalars().first()
    if not job:
         raise HTTPException(status_code=404, detail="Job not found")
         
    if job.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = select(Application).where(Application.job_id == job_id)
    if stage:
        query = query.where(Application.stage == stage)
        
    result = await db.execute(query)
    return result.scalars().all()
