"""
API routes for the application.

This package contains all the API routes and endpoint handlers,
organized by version.
"""

from fastapi import APIRouter

from app.api.v1 import v1_router

# Create a router for all API endpoints
api_router = APIRouter()

# Include versioned router
api_router.include_router(v1_router, prefix="/v1")

# No more direct imports - all endpoints should be versioned
# Legacy routes have been migrated to versioned structure

__all__ = ["api_router"] 