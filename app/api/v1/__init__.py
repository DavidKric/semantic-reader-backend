"""
API routes for v1 of the application.

This package contains all the API routes and endpoint handlers for v1.
Routes are organized by resource/functionality.
"""

from fastapi import APIRouter

# Import all v1 route modules here
from app.api.v1 import health, documents, pipelines, analysis
# Add other route modules as needed: from app.api.v1 import users, items

# Create a router for all v1 endpoints
router = APIRouter()

# Include all resource-specific routers
router.include_router(health.router, tags=["system"])
router.include_router(documents.router, prefix="/documents", tags=["documents"])
router.include_router(pipelines.router, prefix="/pipelines", tags=["pipelines"])
router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
# Add other routers as needed: router.include_router(users.router, prefix="/users", tags=["users"])

__all__ = ["router"] 