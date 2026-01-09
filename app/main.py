from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from app.api.v1.router import api_router
from app.api.v1.exception_handlers import user_not_found_handler, user_already_exists_handler, app_base_exception_handler
from app.core.exceptions import UserNotFoundException, UserAlreadyExistsException, AppBaseException
from app.core.logging import configure_logging
from app.config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    configure_logging()
    logger = structlog.get_logger(__name__)
    logger.info("Application starting up")
    yield
    # Shutdown
    logger.info("Application shutting down")


app = FastAPI(
    title="API Test",
    description="API with Google ADK orchestration",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Get allowed origins from settings - default to localhost for development
allowed_origins = settings.allowed_origins.split(",") if hasattr(settings, 'allowed_origins') and settings.allowed_origins else [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Register exception handlers
app.add_exception_handler(AppBaseException, app_base_exception_handler)
app.add_exception_handler(UserNotFoundException, user_not_found_handler)
app.add_exception_handler(UserAlreadyExistsException, user_already_exists_handler)


@app.get("/", summary="Root endpoint", description="Returns a simple message indicating that the API is running.")
async def root():
    """
    Root endpoint that confirms the API is operational.

    Returns:
        dict: A simple message confirming the API is running.
    """
    return {"message": "API Test is running"}


@app.get("/health", summary="Health check", description="Returns the health status of the API.")
async def health():
    """
    Health check endpoint that returns the current status of the API.

    Returns:
        dict: A dictionary containing the health status.
    """
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)