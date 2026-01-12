from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr
from app.models import UserRole, JobStatus, ApplicationStage

# Token
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# User
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: UserRole
    company_id: Optional[UUID] = None

class UserLogin(UserBase):
    password: str

class UserResponse(UserBase):
    id: UUID
    role: UserRole
    company_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Company
class CompanyBase(BaseModel):
    name: str

class CompanyCreate(CompanyBase):
    pass

class CompanyResponse(CompanyBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

# Job
class JobBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: JobStatus = JobStatus.OPEN

class JobCreate(JobBase):
    pass

class JobUpdate(JobBase):
    pass

class JobResponse(JobBase):
    id: UUID
    company_id: UUID
    created_by: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

# Application History
class ApplicationHistoryResponse(BaseModel):
    id: UUID
    old_stage: Optional[ApplicationStage]
    new_stage: ApplicationStage
    changed_by: UUID
    changed_at: datetime

    class Config:
        from_attributes = True

# Application
class ApplicationBase(BaseModel):
    pass

class ApplicationCreate(ApplicationBase):
    pass # No fields needed, job_id is in URL, candidate from auth

class ApplicationUpdateStage(BaseModel):
    new_stage: ApplicationStage

class ApplicationResponse(BaseModel):
    id: UUID
    job_id: UUID
    candidate_id: UUID
    stage: ApplicationStage
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ApplicationDetailResponse(ApplicationResponse):
    history: List[ApplicationHistoryResponse] = []
