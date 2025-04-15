"""
Recipe API endpoints for document processing.

This module provides FastAPI endpoints for document processing using
Docling directly but maintaining the recipe-based API compatibility.
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import tempfile
import os

from fastapi import APIRouter, File, UploadFile, Form, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import the new converter instead of CoreRecipe
from papermage_docling.converter import convert_document

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Define models
class RecipeOptions(BaseModel):
    """Recipe configuration options."""
    enable_ocr: bool = False
    ocr_language: str = "eng"
    detect_rtl: bool = True
    detect_tables: bool = True
    detect_figures: bool = True
    detect_equations: bool = True
    detect_sections: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "enable_ocr": True,
                "ocr_language": "eng",
                "detect_tables": True,
                "detect_figures": True
            }
        }

class RecipeResponse(BaseModel):
    """Response model for recipe-based processing."""
    job_id: str
    status: str = "completed"
    result: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "result": {
                    "metadata": {"title": "Example Document"},
                    "symbols": "Example text content...",
                    "pages": [{"page_number": 1, "width": 612, "height": 792}]
                }
            }
        }

# Store for processing results
_processing_results = {}

@router.post("/recipe/process", response_model=RecipeResponse, tags=["Recipe"])
async def process_document_with_recipe(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    options: Optional[str] = Form(None)
):
    """
    Process a document using Docling.
    
    This endpoint provides PaperMage-compatible recipe-based document
    processing using Docling directly.
    
    Args:
        file: PDF file to process
        options: JSON string of recipe options
        
    Returns:
        Processing job information and result
    """
    job_id = str(uuid.uuid4())
    logger.info(f"Received recipe processing request, job_id: {job_id}")
    
    # Parse options
    if options:
        import json
        try:
            options_dict = json.loads(options)
            recipe_options = RecipeOptions(**options_dict)
        except Exception as e:
            logger.error(f"Invalid recipe options: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid recipe options: {str(e)}")
    else:
        recipe_options = RecipeOptions()
    
    # Read file content
    content = await file.read()
    
    # Create temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_path = temp_file.name
        temp_file.write(content)
    
    # Process in background
    background_tasks.add_task(
        process_with_docling, 
        temp_path, 
        job_id, 
        recipe_options.dict()
    )
    
    return RecipeResponse(job_id=job_id, status="processing")

@router.get("/recipe/result/{job_id}", response_model=RecipeResponse, tags=["Recipe"])
async def get_recipe_result(job_id: str):
    """
    Get the result of a recipe-based processing job.
    
    Args:
        job_id: ID of the processing job
        
    Returns:
        Job status and result (if available)
    """
    if job_id not in _processing_results:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return _processing_results[job_id]

def process_with_docling(file_path: str, job_id: str, options: Dict[str, Any]):
    """
    Process a document with Docling in the background.
    
    Args:
        file_path: Path to the temporary file
        job_id: Job ID for tracking
        options: Recipe configuration options
    """
    try:
        # Map recipe options to converter options
        converter_options = {
            "detect_tables": options.get("detect_tables", True),
            "detect_figures": options.get("detect_figures", True),
            "enable_ocr": options.get("enable_ocr", False),
            "ocr_language": options.get("ocr_language", "eng"),
        }
        
        # Process document with Docling directly
        logger.info(f"Processing document for job {job_id} with options: {converter_options}")
        result = convert_document(file_path, options=converter_options)
        
        # Store result
        _processing_results[job_id] = RecipeResponse(
            job_id=job_id,
            status="completed",
            result=result
        )
        
        logger.info(f"Completed document processing for job {job_id}")
    
    except Exception as e:
        logger.error(f"Error in document processing: {e}")
        _processing_results[job_id] = RecipeResponse(
            job_id=job_id,
            status="error",
            result={"error": str(e)}
        )
    
    finally:
        # Clean up temp file
        try:
            os.unlink(file_path)
        except:
            pass 