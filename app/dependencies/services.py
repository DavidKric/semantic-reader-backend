"""
Service-related dependencies for injection into routes.

This module provides reusable dependencies for service instances
that can be injected into FastAPI route handlers.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.document_processing_service import DocumentProcessingService
from app.services.pipeline_service import PipelineService


def get_document_service(db: Session = Depends(get_db)) -> DocumentProcessingService:
    """
    Dependency for document processing service with database integration.
    
    Args:
        db: Database session from dependency injection
        
    Returns:
        DocumentProcessingService instance with database integration
    """
    return DocumentProcessingService(db=db)


def get_pipeline_service() -> PipelineService:
    """
    Dependency for pipeline service.
    
    Returns:
        PipelineService instance
    """
    return PipelineService() 