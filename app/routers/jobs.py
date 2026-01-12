from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Job, User, UserRole, JobStatus
from app.schemas import JobCreate, JobResponse, JobUpdate
from app.deps import get_current_user, RoleChecker

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

@router.post("/", response_model=JobResponse)
async def create_job(
    job_in: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.RECRUITER]))
):
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="Recruiter must belong to a company")
        
    job = Job(
        title=job_in.title,
        description=job_in.description,
        status=job_in.status,
        company_id=current_user.company_id,
        created_by=current_user.id
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job

@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Job).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: UUID,
    job_in: JobUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.RECRUITER]))
):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Check permission: Recruiter of the SAME company
    if job.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this job")
        
    job.title = job_in.title
    job.description = job_in.description
    job.status = job_in.status
    
    await db.commit()
    await db.refresh(job)
    return job

@router.delete("/{job_id}")
async def delete_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.RECRUITER]))
):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this job")
        
    await db.delete(job)
    await db.commit()
    return {"message": "Job deleted"}
