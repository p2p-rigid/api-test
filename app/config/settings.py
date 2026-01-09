from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
import re


class Settings(BaseSettings):
    # API Settings
    app_name: str = "API Test"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://postgres:password1234@localhost:5432/api_test"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Google ADK
    google_api_key: Optional[str] = None

    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000"

    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith(('postgresql+asyncpg://', 'postgresql://', 'sqlite://')):
            raise ValueError('Database URL must start with postgresql+asyncpg://, postgresql://, or sqlite://')
        return v

    @field_validator('allowed_origins')
    @classmethod
    def validate_allowed_origins(cls, v: str) -> str:
        """Validate allowed origins format."""
        origins = [origin.strip() for origin in v.split(',') if origin.strip()]
        for origin in origins:
            if not origin.startswith(('http://', 'https://')):
                raise ValueError(f'Origin must start with http:// or https://: {origin}')
        return v

    @field_validator('database_pool_size', 'database_max_overflow')
    @classmethod
    def validate_pool_sizes(cls, v: int) -> int:
        """Validate database pool sizes."""
        if v <= 0:
            raise ValueError('Pool size must be greater than 0')
        if v > 100:
            raise ValueError('Pool size should not exceed 100 for optimal performance')
        return v

    @field_validator('access_token_expire_minutes')
    @classmethod
    def validate_token_expiry(cls, v: int) -> int:
        """Validate access token expiry."""
        if v <= 0:
            raise ValueError('Token expiry must be greater than 0')
        if v > 10080:  # More than a week
            raise ValueError('Token expiry should not exceed 10080 minutes (1 week)')
        return v

    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key strength."""
        if len(v) < 16:
            raise ValueError('Secret key must be at least 16 characters long')
        if v == "your-secret-key-here":
            raise ValueError('Secret key must be changed from default value')
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields from .env file


settings = Settings()