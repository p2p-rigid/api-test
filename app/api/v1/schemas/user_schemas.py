from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
import re


def validate_username(value: str) -> str:
    """Validate username format"""
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]{2,29}$', value):
        raise ValueError(
            "Username must start with a letter and contain only letters, numbers, and underscores"
        )
    return value


def validate_password(value: str) -> str:
    """Validate password strength"""
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r'[A-Z]', value):
        raise ValueError("Password must contain at least 1 uppercase letter")
    if not re.search(r'[a-z]', value):
        raise ValueError("Password must contain at least 1 lowercase letter")
    if not re.search(r'\d', value):
        raise ValueError("Password must contain at least 1 digit")
    if not re.search(r'[!@#$%^&*()_+\-=]', value):
        raise ValueError("Password must contain at least 1 special character (!@#$%^&*()_+-=)")
    return value


def validate_name(value: str) -> str:
    """Validate first/last name format"""
    value = value.strip()
    if not value:
        raise ValueError("Name cannot be empty")
    if len(value) > 50:
        raise ValueError("Name must be 50 characters or less")
    if not re.match(r"^[a-zA-Z\-']+$", value):
        raise ValueError("Name must contain only letters, hyphens, and apostrophes")
    return value


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=30)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)

    @field_validator('username')
    @classmethod
    def check_username(cls, v: str) -> str:
        return validate_username(v)

    @field_validator('first_name', 'last_name')
    @classmethod
    def check_name(cls, v: str) -> str:
        return validate_name(v)


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator('password')
    @classmethod
    def check_password(cls, v: str) -> str:
        return validate_password(v)


class UserUpdate(BaseModel):
    """Schema for updating a user (all fields optional)"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=30)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    is_active: Optional[bool] = None

    @field_validator('username')
    @classmethod
    def check_username(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_username(v)
        return v

    @field_validator('password')
    @classmethod
    def check_password(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_password(v)
        return v

    @field_validator('first_name', 'last_name')
    @classmethod
    def check_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_name(v)
        return v


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
