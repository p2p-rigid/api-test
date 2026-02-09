from typing import Any

from agents.shared.schemas import UserPublic, UsersQueryResult, UsersQueryToolInput
from app.config.database import AsyncSessionLocal
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


async def query_users_tool(
    lookup_type: str,
    user_id: int | None = None,
    email: str | None = None,
    username: str | None = None,
    active_only: bool | None = False,
    skip: int | None = 0,
    limit: int | None = 20,
) -> dict[str, Any]:
    """Read-only users data fetcher exposed to ADK."""

    try:
        tool_input = UsersQueryToolInput(
            lookup_type=lookup_type,
            user_id=user_id,
            email=email,
            username=username,
            active_only=False if active_only is None else active_only,
            skip=0 if skip is None else skip,
            limit=20 if limit is None else limit,
        )
    except Exception as exc:
        result = UsersQueryResult(
            intent="clarification_needed",
            summary="I need a bit more detail to run that users query.",
            error=str(exc),
        )
        return result.model_dump(mode="json")

    async with AsyncSessionLocal() as session:
        user_service = UserService(session)
        user_repository = UserRepository(session)

        try:
            if tool_input.lookup_type == "id" and tool_input.user_id is not None:
                user = await user_service.get_user_by_id(tool_input.user_id)
                users = [user]
                intent = "get_user_by_id"
                filters = {"user_id": tool_input.user_id}
            elif tool_input.lookup_type == "email" and tool_input.email is not None:
                user = await user_service.get_user_by_email(str(tool_input.email))
                users = [user]
                intent = "get_user_by_email"
                filters = {"email": str(tool_input.email)}
            elif tool_input.lookup_type == "username" and tool_input.username is not None:
                user = await user_repository.get_by_username(tool_input.username)
                if user is None:
                    result = UsersQueryResult(
                        intent="get_user_by_username",
                        summary="No user found for that username.",
                        filters={"username": tool_input.username},
                    )
                    return result.model_dump(mode="json")
                users = [user]
                intent = "get_user_by_username"
                filters = {"username": tool_input.username}
            else:
                if tool_input.active_only:
                    users = await user_service.get_active_users(
                        skip=tool_input.skip,
                        limit=tool_input.limit,
                    )
                    intent = "list_active_users"
                else:
                    users = await user_service.get_all_users(
                        skip=tool_input.skip,
                        limit=tool_input.limit,
                    )
                    intent = "list_users"

                filters = {
                    "active_only": tool_input.active_only,
                    "skip": tool_input.skip,
                    "limit": tool_input.limit,
                }
        except Exception as exc:
            result = UsersQueryResult(
                intent="clarification_needed",
                summary="I could not complete that query.",
                error=str(exc),
            )
            return result.model_dump(mode="json")

    payload = [UserPublic.model_validate(user).model_dump(mode="json") for user in users]

    result = UsersQueryResult(
        intent=intent,
        summary=f"Found {len(payload)} user(s).",
        data=[UserPublic.model_validate(item) for item in payload],
        filters=filters,
        count=len(payload),
    )
    return result.model_dump(mode="json")
