"""
Health check endpoints for the application.

This module provides endpoints for checking the health and status
of the application and its dependencies.
"""

from fastapi import APIRouter, status

from app.core.config import settings
from app.schemas.health import HealthResponse, DetailedHealthResponse, VersionResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["system"],
    summary="Basic Health Check",
    description="Get basic health status of the API"
)
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint.
    
    Returns a simple health status for basic monitoring.
    """
    return HealthResponse(
        status="ok",
    )


@router.get(
    "/health/detail",
    response_model=DetailedHealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["system"],
    summary="Detailed Health Check",
    description="Get detailed health status of the API and its components"
)
async def detailed_health_check() -> DetailedHealthResponse:
    """
    Detailed health check endpoint.
    
    Checks the status of all major components and returns detailed health information.
    """
    components = {
        "app": "ok"
    }
    
    # Try to check if the document processing pipeline is available
    try:
        from papermage_docling.api_service import get_api_service
        api_service = get_api_service()
        components["document_processing"] = "ok"
    except Exception:
        components["document_processing"] = "not_configured"
    
    # Overall status is ok only if all components are ok
    status_value = "ok" if all(v == "ok" for v in components.values()) else "degraded"
    
    return DetailedHealthResponse(
        status=status_value,
        components=components
    )


@router.get(
    "/version",
    response_model=VersionResponse,
    status_code=status.HTTP_200_OK,
    tags=["system"],
    summary="Version Information",
    description="Get version information about the API"
)
async def get_version() -> VersionResponse:
    """
    Version information endpoint.
    
    Returns the version information for the API.
    """
    return VersionResponse(
        version=settings.APP_VERSION,
        api_version=settings.API_VERSION,
        commit=getattr(settings, "COMMIT_HASH", None)
    ) 