import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://ats_user:ats_password@localhost:5432/ats_db"
    JWT_SECRET_KEY: str = "your-super-secret-key-change-this"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    REDIS_URL: str = "redis://localhost:6379/0"
    
    SENDGRID_API_KEY: str = "SG.mock"
    FROM_EMAIL: str = "noreply@ats.example.com"
    
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
