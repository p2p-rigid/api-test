from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.api.v1.schemas.agent_schemas import UsersNlQueryRequest, UsersNlQueryResponse
from app.config.settings import settings
from app.services.users_nl_query_service import UsersNlQueryService, get_users_nl_query_service

router = APIRouter()


@router.post("/users/query", response_model=UsersNlQueryResponse, status_code=status.HTTP_200_OK)
async def query_users_natural_language(
    payload: UsersNlQueryRequest,
    x_user_id: Optional[str] = Header(default=None, alias="X-User-ID"),
    query_service: UsersNlQueryService = Depends(get_users_nl_query_service),
) -> UsersNlQueryResponse:
    """Execute read-only natural-language queries against users."""

    user_id = x_user_id or "api_user"
    requested_limit = payload.limit if payload.limit is not None else settings.users_nl_default_limit
    limit = min(requested_limit, settings.users_nl_max_limit)

    try:
        result = await query_service.query_users(
            query=payload.query,
            user_id=user_id,
            session_id=payload.session_id,
            limit=limit,
            provider=payload.provider,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process natural-language user query.",
        ) from exc

    result.filters = {**result.filters, "limit": limit, "provider": payload.provider}
    return UsersNlQueryResponse.model_validate(result.model_dump(mode="json"))
