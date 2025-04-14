"""
Document conversion endpoints.

This module provides endpoints for converting documents from various formats
to structured data, with support for both URL and file upload inputs.
"""

import logging
import json
import uuid
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, File, UploadFile, Form, BackgroundTasks, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.models import (
    ConvertURLRequest, ConvertResponse, JobStatusResponse,
    ConversionOptions, DocumentResult
)
from app.pipelines import document_processor, job_store
from app.config import settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix=f"/{settings.API_VERSION}", tags=["Document Conversion"])

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
    summary="Convert uploaded documents",
    description="Process uploaded document files and convert them to structured data."
)
async def convert_from_file(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    options: Optional[str] = Form(None)
) -> ConvertResponse:
    """
    Process uploaded document files.
    
    Args:
        background_tasks: FastAPI background tasks
        files: List of uploaded files to process
        options: JSON string of conversion options
        
    Returns:
        Job information and status
    """
    logger.info(f"Received request to convert {len(files)} uploaded files")
    
    # Parse options
    conversion_options = None
    if options:
        try:
            options_dict = json.loads(options)
            conversion_options = ConversionOptions(**options_dict).dict()
        except Exception as e:
            logger.error(f"Invalid conversion options: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid conversion options: {str(e)}")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Process in background
    background_tasks.add_task(
        document_processor.process_file_documents,
        files,
        job_id,
        conversion_options
    )
    
    return ConvertResponse(job_id=job_id, status="processing")

@router.get(
    "/job/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status",
    description="Check the status of a document processing job and retrieve results if available."
)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Get the status of a document processing job.
    
    Args:
        job_id: ID of the processing job
        
    Returns:
        Job status and results (if available)
        
    Raises:
        HTTPException: If job not found
    """
    logger.info(f"Checking status for job {job_id}")
    
    job_data = job_store.get_job_status(job_id)
    if not job_data:
        logger.warning(f"Job {job_id} not found")
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Convert to response model
    response = JobStatusResponse(
        job_id=job_id,
        status=job_data.get("status", "processing"),
        created_at=job_data.get("created_at", ""),
        updated_at=job_data.get("updated_at"),
        results=None
    )
    
    # Add results if available
    if job_data.get("status") == "completed" and "results" in job_data:
        results = []
        for result in job_data["results"]:
            document_result = DocumentResult(
                status=result.get("status", "failed"),
                document=result.get("document") if result.get("status") == "success" else None,
                error=result.get("error"),
                filename=result.get("filename"),
                url=result.get("url")
            )
            results.append(document_result)
        
        response.results = results
    
    return response 