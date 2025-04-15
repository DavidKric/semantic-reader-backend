"""
Document conversion endpoints.

This module provides endpoints for converting documents from various formats
to structured data, with support for both URL and file upload inputs.
"""

import logging
import json
import uuid
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, File, UploadFile, Form, BackgroundTasks, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from app.models import (
    ConvertURLRequest, ConvertResponse, JobStatusResponse,
    ConversionOptions, DocumentResult
)
from app.pipelines import document_processor, job_store
from app.dependencies.services import get_document_service
from app.services.document_processing_service import DocumentProcessingService
from app.config import settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Document Conversion"])

@router.post(
    "/convert/url",
    response_model=ConvertResponse,
    summary="Convert documents from URLs",
    description="Process documents from provided URLs and convert them to structured data."
)
async def convert_from_url(
    request: ConvertURLRequest,
    background_tasks: BackgroundTasks
) -> ConvertResponse:
    """
    Process documents from URLs.
    
    Args:
        request: URL conversion request with options
        background_tasks: FastAPI background tasks
        
    Returns:
        Job information and status
    """
    logger.info(f"Received request to convert {len(request.urls)} URLs")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Process in background
    background_tasks.add_task(
        document_processor.process_url_documents,
        request.urls,
        job_id,
        request.options.dict() if request.options else None
    )
    
    return ConvertResponse(job_id=job_id, status="processing")

@router.post(
    "/convert/file",
    response_model=ConvertResponse,
    summary="Convert document from file upload",
    description="Process an uploaded document and convert it to structured data."
)
async def convert_from_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    options: Optional[str] = Form(None),
    document_service: DocumentProcessingService = Depends(get_document_service)
) -> ConvertResponse:
    """
    Process an uploaded document.
    
    Args:
        background_tasks: FastAPI background tasks
        file: Document file to process
        options: JSON string of conversion options
        document_service: Document processing service from dependency injection
        
    Returns:
        Job information and status
    """
    # Generate job ID
    job_id = str(uuid.uuid4())
    logger.info(f"Received file conversion request, job_id: {job_id}")
    
    # Parse options
    conversion_options = {}
    if options:
        try:
            options_dict = json.loads(options)
            conversion_options = ConversionOptions(**options_dict).dict()
        except Exception as e:
            logger.error(f"Invalid conversion options: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Invalid conversion options: {str(e)}"
            )
    
    # Process in background
    background_tasks.add_task(
        document_processor.process_uploaded_document,
        file,
        job_id,
        conversion_options
    )
    
    return ConvertResponse(job_id=job_id, status="processing")

@router.get(
    "/convert/status/{job_id}",
    response_model=JobStatusResponse,
    summary="Get conversion job status",
    description="Get the status and result of a document conversion job."
)
async def get_conversion_status(job_id: str) -> JobStatusResponse:
    """
    Get the status of a document conversion job.
    
    Args:
        job_id: ID of the conversion job
        
    Returns:
        Job status and result (if available)
        
    Raises:
        HTTPException: If job not found
    """
    logger.info(f"Checking status for conversion job {job_id}")
    
    job_data = job_store.get_job_status(job_id)
    if not job_data:
        logger.warning(f"Conversion job {job_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Job not found"
        )
    
    # Convert internal job status to response model
    response = JobStatusResponse(
        job_id=job_id,
        status=job_data.get("status", "processing"),
        documents=job_data.get("documents", []),
        progress=job_data.get("progress", 0),
        total=job_data.get("total", 0),
        errors=job_data.get("errors", [])
    )
    
    return response 