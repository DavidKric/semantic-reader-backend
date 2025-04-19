"""
Recipe-based document processing endpoints.

This module provides endpoints for processing documents using the PaperMage-compatible
recipe API, which mimics the CoreRecipe functionality from PaperMage.
"""

import json
import logging
import os
import tempfile
import uuid
from typing import Any, Dict, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field

from app.dependencies.services import get_document_service
from app.models import ConversionOptions
from app.pipelines import job_store
from app.services.document_processing_service import DocumentProcessingService
from papermage_docling.recipe import CoreRecipe

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Recipe API"])

# Define recipe-specific models
class RecipeResponse(BaseModel):
    """Response model for recipe-based processing."""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "processing"
    result: Optional[Dict[str, Any]] = None

@router.post(
    "/recipe/process",
    response_model=RecipeResponse,
    summary="Process document with recipe",
    description="Process a document using PaperMage-compatible CoreRecipe."
)
async def process_document_with_recipe(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    options: Optional[str] = Form(None),
    document_service: DocumentProcessingService = Depends(get_document_service)
) -> RecipeResponse:
    """
    Process a document using CoreRecipe.
    
    Args:
        background_tasks: FastAPI background tasks
        file: PDF file to process
        options: JSON string of recipe options
        document_service: Document processing service from dependency injection
        
    Returns:
        Job information and status
    """
    job_id = str(uuid.uuid4())
    logger.info(f"Received recipe processing request, job_id: {job_id}")
    
    # Parse options
    recipe_options = {}
    if options:
        try:
            options_dict = json.loads(options)
            conversion_options = ConversionOptions(**options_dict)
            recipe_options = {
                "enable_ocr": conversion_options.perform_ocr,
                "ocr_language": conversion_options.ocr_language,
                "detect_rtl": conversion_options.detect_rtl,
                "detect_tables": conversion_options.extract_tables,
                "detect_figures": conversion_options.extract_figures,
                "detect_equations": conversion_options.extract_equations,
                "detect_sections": conversion_options.extract_sections,
            }
        except Exception as e:
            logger.error(f"Invalid recipe options: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Invalid recipe options: {str(e)}"
            )
    
    # Process in background (use job store for state persistence)
    # Initialize job in job store
    job_store.create_job(job_id)
    
    # Read file content
    content = await file.read()
    
    # Create temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_path = temp_file.name
        temp_file.write(content)
    
    # Process in background
    background_tasks.add_task(
        process_with_recipe, 
        temp_path, 
        job_id, 
        recipe_options,
        document_service
    )
    
    return RecipeResponse(job_id=job_id, status="processing")

@router.get(
    "/recipe/result/{job_id}",
    response_model=RecipeResponse,
    summary="Get recipe processing result",
    description="Get the result of a recipe-based document processing job."
)
async def get_recipe_result(job_id: str) -> RecipeResponse:
    """
    Get the result of a recipe-based processing job.
    
    Args:
        job_id: ID of the processing job
        
    Returns:
        Job status and result (if available)
        
    Raises:
        HTTPException: If job not found
    """
    logger.info(f"Checking result for recipe job {job_id}")
    
    job_data = job_store.get_job_status(job_id)
    if not job_data:
        logger.warning(f"Recipe job {job_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Job not found"
        )
    
    return RecipeResponse(
        job_id=job_id,
        status=job_data.get("status", "processing"),
        result=job_data.get("result")
    )

def process_with_recipe(
    file_path: str, 
    job_id: str, 
    options: Dict[str, Any],
    document_service: Optional[DocumentProcessingService] = None
) -> None:
    """
    Process a document with CoreRecipe in the background.
    
    Args:
        file_path: Path to the temporary file
        job_id: Job ID for tracking
        options: Recipe configuration options
        document_service: Document processing service (optional)
    """
    try:
        # Create recipe
        recipe = CoreRecipe(**options)
        
        # Process document
        logger.info(f"Processing document with CoreRecipe for job {job_id}")
        result = recipe.run(file_path)
        
        # Convert result to JSON-serializable format
        if hasattr(result, 'to_json'):
            json_result = result.to_json()
        elif hasattr(result, '__dict__'):
            json_result = result.__dict__
        else:
            json_result = {"content": str(result)}
        
        # Store document in database if document_service is provided
        if document_service:
            try:
                # Create a database entry for the document
                db_document = document_service.create(
                    filename=os.path.basename(file_path),
                    file_type="pdf",
                    processing_status="completed",
                    is_processed=True,
                    storage_id=job_id,
                    doc_metadata=options,
                    # Extract metadata from result
                    language=json_result.get("metadata", {}).get("language", ""),
                    has_rtl=json_result.get("metadata", {}).get("is_rtl_language", False),
                    num_pages=len(json_result.get("pages", [])),
                    word_count=len(json_result.get("words", []))
                )
                
                logger.info(f"Created database entry for document: {db_document.id}")
                
                # Add document ID to result
                json_result["database_id"] = db_document.id
                
            except Exception as e:
                logger.error(f"Error saving document to database: {e}")
                # Continue with the process even if database save fails
        
        # Store result
        job_store.update_job(job_id, {
            "status": "completed",
            "result": json_result
        })
        
        logger.info(f"Completed recipe processing for job {job_id}")
    
    except Exception as e:
        logger.error(f"Error in recipe processing: {e}")
        job_store.update_job(job_id, {
            "status": "failed",
            "result": {"error": str(e)}
        })
    
    finally:
        # Clean up temp file
        try:
            os.unlink(file_path)
        except:
            pass 