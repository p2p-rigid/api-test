from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from agents.shared.schemas import UserPublic


class UsersNlQueryRequest(BaseModel):
    """Input for NL users query endpoint."""

    query: str = Field(..., min_length=1, max_length=500)
    limit: Optional[int] = Field(default=None, ge=1)
    provider: Literal["google", "openrouter"] = "google"


class UsersNlQueryResponse(BaseModel):
    """Structured output returned by NL users query endpoint."""

    summary: str
    intent: Literal[
        "get_user_by_id",
        "get_user_by_email",
        "get_user_by_username",
        "list_users",
        "list_active_users",
        "clarification_needed",
        "out_of_scope",
    ]
    data: list[UserPublic] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)
    count: int = 0
    error: Optional[str] = None

    model_config = ConfigDict(extra="forbid")
