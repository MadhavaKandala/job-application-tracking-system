from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, jobs, applications, companies

app = FastAPI(
    title="Job Application Tracking System",
    description="API for managing job applications with RBAC and Workflow",
    version="1.0.0"
)

# CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(companies.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to ATS API"}
