"""
Database-related dependencies for injection into routes and services.

This module provides reusable dependencies for database access
that can be injected into FastAPI route handlers and services.
"""

from fastapi import Depends

from app.core.database import get_db

# Re-export the get_db function as a FastAPI dependency
# This allows routes to use Depends(get_db) to inject a database session
db_dependency = Depends(get_db) 