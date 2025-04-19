"""
Version 1 of the API.

This module defines the v1 API router and includes all the v1 API endpoints.
"""

from fastapi import APIRouter

# Import all v1 route modules here
from app.api.v1 import analysis, convert, documents, health, pipelines

# Add other route modules as needed: from app.api.v1 import users, items

# Create the v1 router
v1_router = APIRouter()

# Include all resource-specific routers
v1_router.include_router(health.router, prefix="/health", tags=["Health"])
v1_router.include_router(documents.router, tags=["Documents"])
v1_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
v1_router.include_router(pipelines.router, prefix="/pipelines", tags=["Pipelines"])
v1_router.include_router(convert.router, tags=["Conversion"])
# Add other routers as needed: v1_router.include_router(users.router, prefix="/users", tags=["users"])

__all__ = ["v1_router"] 