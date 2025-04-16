"""
Pipeline API endpoints for document processing.

This module provides endpoints for managing document processing pipelines,
configuration, and statistics.
"""

import logging
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.pipeline_service import PipelineService

router = APIRouter()
logger = logging.getLogger(__name__)

# Remove direct imports from papermage_docling modules

@router.get("/pipeline/config")
async def get_pipeline_config(
    db: AsyncSession = Depends(get_db)
):
    """
    Get current document processing configuration.
    
    Returns:
        Pipeline configuration
    """
    # Create pipeline service
    pipeline_service = PipelineService(db)
    
    try:
        # Get pipeline configuration
        config = pipeline_service.get_pipeline_config()
        
        return {
            "status": "success",
            "config": config
        }
    except Exception as e:
        logger.error(f"Error getting pipeline configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting pipeline configuration: {str(e)}")

@router.put("/pipeline/config")
async def update_pipeline_config(
    config: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Update document processing configuration.
    
    Args:
        config: Configuration to update
        db: Database session
        
    Returns:
        Updated pipeline configuration
    """
    # Create pipeline service
    pipeline_service = PipelineService(db)
    
    try:
        # Update pipeline configuration
        updated_config = pipeline_service.update_pipeline_config(config)
        
        return {
            "status": "success",
            "config": updated_config
        }
    except Exception as e:
        logger.error(f"Error updating pipeline configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating pipeline configuration: {str(e)}")

@router.get("/pipeline/stats")
async def get_pipeline_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Get document processing statistics.
    
    Returns:
        Pipeline statistics
    """
    # Create pipeline service
    pipeline_service = PipelineService(db)
    
    try:
        # Get pipeline statistics
        stats = pipeline_service.get_pipeline_stats()
        
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting pipeline statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting pipeline statistics: {str(e)}")

@router.post("/process")
async def process_document(
    document_path: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
):
    """
    Process a document using the current configuration.
    
    Args:
        document_path: Path to the document
        db: Database session
        
    Returns:
        Processed document data
    """
    # Create pipeline service
    pipeline_service = PipelineService(db)
    
    try:
        # Process the document
        result = pipeline_service.process_document(document_path)
        
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}") 