"""
API routes for the application.

This package contains all the API routes and endpoint handlers.
Routes are organized by resource/functionality and API version.
"""

from fastapi import APIRouter

from app.api.v1 import router as v1_router

# Main router that includes all API versions
api_router = APIRouter()

# Include versioned routers
api_router.include_router(v1_router, prefix="/v1")

__all__ = ["api_router"] 