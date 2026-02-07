"""Health check endpoint."""

from fastapi import APIRouter

from ...config.settings import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring.

    Returns:
        dict: Health status and version info
    """
    return {
        "status": "healthy",
        "version": settings.app_version,
        "service": "AB Testing Agent API",
    }
