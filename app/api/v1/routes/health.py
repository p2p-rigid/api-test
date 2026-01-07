from fastapi import APIRouter

router = APIRouter()


@router.get("", tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "version": "0.1.0"
    }


@router.get("/ready", tags=["health"])
async def readiness_check():
    # TODO: Add database connectivity check
    return {
        "status": "ready",
        "database": "connected"
    }