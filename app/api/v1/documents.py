"""
Document processing endpoints for the application.

This module provides endpoints for document processing, parsing,
and conversion using the Docling document processing pipeline.
"""

import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query, status
from fastapi.responses import JSONResponse

from app.core.config import settings
# Import papermage_docling API service
try:
    from papermage_docling.api_service import get_api_service
    DOCLING_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("papermage_docling not available. Document processing features will be disabled.")
    DOCLING_AVAILABLE = False

from app.schemas.documents import (
    DocumentResponse,
    PaperMageResponse,
    DocumentListResponse,
    ProcessDocumentRequest,
    DocumentProcessingOptions
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post(
    "/parse",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    tags=["documents"],
    summary="Parse Document",
    description="Parse a document file (PDF, DOCX, TXT) and extract structured content"
)
async def parse_document(
    file: UploadFile = File(...),
    page_range: Optional[str] = Form(None),
    detect_rtl: Optional[bool] = Form(None),
    output_format: str = Form("docling"),
    save_document: bool = Form(True)
) -> DocumentResponse:
    """
    Parse a document file and extract structured content.
    
    This endpoint processes a document file and returns the structured content
    using the Docling document processing pipeline.
    
    Args:
        file: The document file to parse (PDF, DOCX, or TXT)
        page_range: Optional range of pages to parse (e.g., "1-5,7,9-11")
        detect_rtl: Whether to detect and handle right-to-left text
        output_format: Output format (docling or papermage)
        save_document: Whether to save the processed document
    
    Returns:
        The processed document in the requested format
    """
    # Check if papermage_docling is available
    if not DOCLING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Document processing service is not available"
        )
    
    # Check file type
    allowed_extensions = getattr(settings, "ALLOWED_EXTENSIONS", ["pdf", "docx", "txt"])
    file_ext = Path(file.filename).suffix.lower().lstrip('.')
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Check file size
    max_size = getattr(settings, "MAX_FILE_SIZE_MB", 10) * 1024 * 1024  # Convert to bytes
    file_content = await file.read()
    
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {getattr(settings, 'MAX_FILE_SIZE_MB', 10)}MB"
        )
    
    # Prepare processing options
    options = {}
    
    # Parse page range
    if page_range:
        try:
            page_list = []
            for part in page_range.split(','):
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    page_list.extend(range(start, end + 1))
                else:
                    page_list.append(int(part))
            options['page_range'] = page_list
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid page range format: {page_range}. Use format like '1-5,7,9-11'"
            )
    
    # Set RTL detection
    if detect_rtl is not None:
        options['detect_rtl'] = detect_rtl
    else:
        options['detect_rtl'] = getattr(settings, "DETECT_RTL", True)
    
    # Set output format
    return_papermage = output_format.lower() == 'papermage'
    options['return_papermage'] = return_papermage
    
    try:
        # Get API service
        api_service = get_api_service()
        
        # Process document
        with tempfile.NamedTemporaryFile(suffix=f".{file_ext}", delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file.flush()
            
            result = api_service.process_document(
                temp_file.name,
                save_result=save_document,
                return_id=False,
                **options
            )
        
        # Return processed document
        if return_papermage:
            return PaperMageResponse(
                status="success",
                document_id=getattr(result, "id", None),
                data=result
            )
        else:
            return DocumentResponse(
                status="success",
                document_id=getattr(result, "id", None),
                data=result if hasattr(result, "__dict__") else result.__dict__
            )
            
    except Exception as e:
        logger.exception(f"Error processing document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    tags=["documents"],
    summary="Get Document",
    description="Get a previously processed document by ID"
)
async def get_document(
    document_id: str,
    output_format: str = Query("docling", description="Output format (docling or papermage)")
) -> DocumentResponse:
    """
    Get a processed document by ID.
    
    Args:
        document_id: The document ID
        output_format: Output format (docling or papermage)
    
    Returns:
        The document in the requested format
    """
    # Check if papermage_docling is available
    if not DOCLING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Document processing service is not available"
        )
    
    try:
        # Get API service
        api_service = get_api_service()
        
        # Get document
        as_papermage = output_format.lower() == 'papermage'
        result = api_service.get_document(document_id, as_papermage=as_papermage)
        
        # Return document
        if as_papermage:
            return PaperMageResponse(
                status="success",
                document_id=document_id,
                data=result
            )
        else:
            return DocumentResponse(
                status="success",
                document_id=document_id,
                data=result if hasattr(result, "__dict__") else result.__dict__
            )
            
    except Exception as e:
        logger.exception(f"Error retrieving document: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Document not found or error retrieving document: {str(e)}"
        )


@router.get(
    "",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    tags=["documents"],
    summary="List Documents",
    description="List available processed documents"
)
async def list_documents() -> DocumentListResponse:
    """
    List available processed documents.
    
    Returns:
        List of document metadata
    """
    # Check if papermage_docling is available
    if not DOCLING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Document processing service is not available"
        )
    
    try:
        # Get API service
        api_service = get_api_service()
        
        # List documents
        documents = api_service.list_documents()
        
        return DocumentListResponse(
            status="success",
            count=len(documents),
            documents=documents
        )
            
    except Exception as e:
        logger.exception(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing documents: {str(e)}"
        )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["documents"],
    summary="Delete Document",
    description="Delete a processed document by ID"
)
async def delete_document(document_id: str):
    """
    Delete a processed document by ID.
    
    Args:
        document_id: The document ID
    """
    # Check if papermage_docling is available
    if not DOCLING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Document processing service is not available"
        )
    
    try:
        # Get API service
        api_service = get_api_service()
        
        # Delete document
        success = api_service.delete_document(document_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {document_id}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        ) 