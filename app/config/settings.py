from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Settings
    app_name: str = "API Test"
    debug: bool = False
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/api_test"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Google ADK
    google_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()