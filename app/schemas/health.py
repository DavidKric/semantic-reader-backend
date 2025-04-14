"""
Health-related schemas for request/response validation.

This module contains Pydantic models for health-related endpoints.
"""

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base import BaseSchema


class HealthResponse(BaseSchema):
    """Response model for health check endpoint."""
    status: str = "ok"
    timestamp: datetime = Field(default_factory=datetime.now)


class DetailedHealthResponse(HealthResponse):
    """Detailed health check response with component statuses."""
    
    components: dict


class VersionResponse(BaseSchema):
    """Response model for version endpoint."""
    version: str
    api_version: str
    commit: Optional[str] = None 