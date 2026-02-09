from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class UserPublic(BaseModel):
    """Sanitized user representation returned by NL query flows."""

    id: int
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UsersQueryToolInput(BaseModel):
    """Validated input for the read-only users query tool."""

    lookup_type: Literal["id", "email", "username", "list"]
    user_id: Optional[int] = Field(default=None, ge=1)
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    active_only: bool = False
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def validate_lookup_requirements(self) -> "UsersQueryToolInput":
        if self.lookup_type == "id" and self.user_id is None:
            raise ValueError("user_id is required when lookup_type='id'")

        if self.lookup_type == "email" and self.email is None:
            raise ValueError("email is required when lookup_type='email'")

        if self.lookup_type == "username":
            if self.username is None or not self.username.strip():
                raise ValueError("username is required when lookup_type='username'")

        if self.lookup_type != "list" and (self.skip != 0 or self.limit != 20):
            raise ValueError("skip/limit are only valid when lookup_type='list'")

        return self


class UsersQueryResult(BaseModel):
    """Structured output from the read-only users query tool."""

    intent: Literal[
        "get_user_by_id",
        "get_user_by_email",
        "get_user_by_username",
        "list_users",
        "list_active_users",
        "clarification_needed",
        "out_of_scope",
    ]
    summary: str
    data: list[UserPublic] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)
    count: int = 0
    error: Optional[str] = None

    model_config = ConfigDict(extra="forbid")
