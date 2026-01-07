from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException,
)


async def user_not_found_handler(request: Request, exc: UserNotFoundException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc), "identifier": exc.identifier},
    )


async def user_already_exists_handler(request: Request, exc: UserAlreadyExistsException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": str(exc),
            "field": exc.field,
            "value": exc.value,
        },
    )
