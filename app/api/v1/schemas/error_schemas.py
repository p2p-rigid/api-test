"""
Error response schemas for standardized error handling.
"""
from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum


class ErrorCode(str, Enum):
    """Enumeration of standard error codes."""
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorResponse(BaseModel):
    """Standardized error response model."""
    error_code: ErrorCode
    message: str
    details: Optional[Any] = None
    field: Optional[str] = None
    value: Optional[str] = None
    
    class Config:
        use_enum_values = True


class ValidationErrorDetail(BaseModel):
    """Detailed validation error information."""
    loc: list[str] = Field(..., description="Location of the validation error")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")