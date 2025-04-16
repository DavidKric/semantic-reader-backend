"""
Health check endpoints for the API.
"""

import logging
import platform
import sys
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.api.deps import get_db
from app.services.document_processing_service import DocumentProcessingService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health", response_model=Dict[str, Any])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint.
    
    Returns information about the API health status, including:
    - API version
    - Database status
    - Document processing status
    - System information
    """
    # Base health response
    health_data = {
        "status": "ok",
        "version": settings.VERSION,
        "env": settings.ENVIRONMENT,
        "system": {
            "python_version": platform.python_version(),
            "system": platform.system(),
            "node": platform.node()
        }
    }
    
    # Check database connection
    try:
        # Simple database query
        result = await db.execute("SELECT 1")
        health_data["database"] = {
            "status": "ok",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_data["database"] = {
            "status": "error",
            "message": f"Database connection failed: {str(e)}"
        }
        health_data["status"] = "degraded"
    
    # Check docling availability
    try:
        # Check if papermage_docling is available
        try:
            from papermage_docling.converter import convert_document
            
            # Report Docling status
            health_data["document_processing"] = {
                "status": "ok",
                "converter": "docling.document_converter.DocumentConverter",
                "parser": "doclingparse_v4",
                "rtl_support": True
            }
        except ImportError:
            health_data["document_processing"] = {
                "status": "unavailable",
                "message": "papermage_docling module not available"
            }
            health_data["status"] = "degraded"
    except Exception as e:
        health_data["document_processing"] = {
            "status": "error",
            "message": f"Error checking document processing: {str(e)}"
        }
        health_data["status"] = "degraded"
    
    return health_data

@router.get("/version")
async def get_version():
    """
    Get the API version.
    """
    return {
        "version": settings.VERSION,
        "env": settings.ENVIRONMENT
    } 