from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException,
    AppBaseException
)
from app.api.v1.schemas.error_schemas import ErrorResponse


async def app_base_exception_handler(request: Request, exc: AppBaseException) -> JSONResponse:
    """General handler for all app base exceptions."""
    error_response = ErrorResponse(
        error_code=exc.error_code,
        message=exc.message,
        field=getattr(exc, 'field', None),
        value=getattr(exc, 'value', None),
        details=getattr(exc, 'details', None)
    )

    # Map error codes to HTTP status codes
    status_map = {
        "USER_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "USER_ALREADY_EXISTS": status.HTTP_409_CONFLICT,
        "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "DATABASE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "UNAUTHORIZED": status.HTTP_401_UNAUTHORIZED,
        "FORBIDDEN": status.HTTP_403_FORBIDDEN,
        "INTERNAL_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }

    http_status = status_map.get(exc.error_code.value, status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JSONResponse(
        status_code=http_status,
        content=error_response.dict(),
    )


async def user_not_found_handler(request: Request, exc: UserNotFoundException) -> JSONResponse:
    """Handler for user not found exceptions."""
    return await app_base_exception_handler(request, exc)


async def user_already_exists_handler(request: Request, exc: UserAlreadyExistsException) -> JSONResponse:
    """Handler for user already exists exceptions."""
    return await app_base_exception_handler(request, exc)
