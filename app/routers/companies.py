from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Company
from app.schemas import CompanyCreate, CompanyResponse

router = APIRouter(tags=["Companies"])

@router.post("/api/companies", response_model=CompanyResponse)
async def create_company(company: CompanyCreate, db: AsyncSession = Depends(get_db)):
    db_company = Company(name=company.name)
    db.add(db_company)
    await db.commit()
    await db.refresh(db_company)
    return db_company
