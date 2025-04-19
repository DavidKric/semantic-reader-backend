"""
Health and version endpoints.

This module provides health check and version information endpoints
for monitoring and status verification.
"""

import logging

from fastapi import APIRouter, status

from app.config import settings
from app.models import HealthResponse, VersionResponse

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Health"])

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    description="Verify the service is up and running."
)
async def health_check() -> HealthResponse:
    """Health check endpoint to verify service is running."""
    logger.debug("Health check requested")
    return HealthResponse()

@router.get(
    "/version",
    response_model=VersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Version information",
    description="Get the service version information."
)
async def version() -> VersionResponse:
    """Return application version information."""
    logger.debug("Version information requested")
    return VersionResponse(
        version=settings.APP_VERSION,
        api_version=settings.API_VERSION,
        commit=settings.commit_hash
    ) 