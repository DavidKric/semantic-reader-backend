"""
Document processing endpoints for the application.

This module provides endpoints for document processing, parsing,
and conversion using the local database models and optionally the 
Docling document processing pipeline.
"""

import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.dependencies.services import get_document_service
from app.services.document_processing_service import DocumentProcessingService
from app.schemas.documents import (
    DocumentResponse,
    PaperMageResponse,
    DocumentListResponse,
    ProcessDocumentRequest,
    DocumentProcessingOptions
)

# Import papermage_docling API service
try:
    from papermage_docling.api_service import get_api_service
    DOCLING_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("papermage_docling not available. Document processing features will be disabled.")
    DOCLING_AVAILABLE = False

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", response_model=Dict[str, str])
async def document_health(
    document_service: DocumentProcessingService = Depends(get_document_service)
):
    """
    Check if the document service is available.
    
    Returns:
        Status information for the document service
    """
    # Check if external API is available
    external_api_status = "available" if document_service.external_api_available else "unavailable"
    
    # Check if database is available
    db_status = "connected"
    
    return {
        "status": "ok", 
        "database": db_status,
        "external_api": external_api_status
    }


@router.post("/parse", response_model=DocumentResponse)
async def parse_document(
    file: UploadFile = File(...),
    options: Optional[DocumentProcessingOptions] = None,
    document_service: DocumentProcessingService = Depends(get_document_service)
):
    """
    Parse a document using the appropriate parser.
    
    Args:
        file: The document file
        options: Additional parsing options
        document_service: Document processing service from dependency injection
        
    Returns:
        Parsed document data
    """
    # Set default options if not provided
    if options is None:
        options = DocumentProcessingOptions()
    
    # Get file extension from filename
    file_ext = Path(file.filename).suffix.lstrip('.')
    
    # Check if file extension is allowed
    if file_ext.lower() not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file_ext}' not supported. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Convert options to dict
    options_dict = options.model_dump() if hasattr(options, 'model_dump') else options.dict()
    
    try:
        # Process document using service - now uses database
        document = await document_service.parse_document(
            document=file,
            file_type=file_ext.lower(),
            options=options_dict
        )
        
        # Convert document to response model
        return DocumentResponse.model_validate(document) if hasattr(DocumentResponse, 'model_validate') else DocumentResponse.from_orm(document)
    
    except Exception as e:
        logger.error(f"Error parsing document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse document: {str(e)}"
        )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    as_papermage: bool = Query(False, description="Return in PaperMage format"),
    document_service: DocumentProcessingService = Depends(get_document_service)
):
    """
    Get a document by ID.
    
    Args:
        document_id: The document ID
        as_papermage: Whether to return in PaperMage format
        document_service: Document processing service from dependency injection
        
    Returns:
        The document data
    """
    try:
        # Get document from service
        document = await document_service.get_document(document_id, as_papermage=as_papermage)
        
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID '{document_id}' not found"
            )
        
        # If as_papermage is True and document is a dict (not a model), return as PaperMage format
        if as_papermage and not hasattr(document, 'id'):
            return document
        
        # Convert document to response model
        return DocumentResponse.model_validate(document) if hasattr(DocumentResponse, 'model_validate') else DocumentResponse.from_orm(document)
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )


@router.delete("/documents/{document_id}", response_model=Dict[str, bool])
async def delete_document(
    document_id: str,
    document_service: DocumentProcessingService = Depends(get_document_service)
):
    """
    Delete a document by ID.
    
    Args:
        document_id: The document ID
        document_service: Document processing service from dependency injection
        
    Returns:
        Success status
    """
    try:
        # Delete document using service
        success = await document_service.delete_document(document_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID '{document_id}' not found"
            )
        
        return {"success": True}
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    include_external: bool = Query(True, description="Include documents from external storage"),
    sync_with_external: bool = Query(True, description="Sync external documents with local database"),
    document_service: DocumentProcessingService = Depends(get_document_service)
):
    """
    List available documents.
    
    Args:
        page: Page number for pagination
        page_size: Number of items per page
        include_external: Whether to include documents from external storage
        sync_with_external: Whether to sync external documents with local database
        document_service: Document processing service from dependency injection
        
    Returns:
        List of document metadata
    """
    try:
        # Get documents from service with pagination
        documents = await document_service.list_documents(
            include_external=include_external,
            sync_with_external=sync_with_external,
            page=page,
            page_size=page_size
        )
        
        # Get total count for pagination
        total_count = document_service.get_document_count()
        
        # Convert to response model
        document_list = [
            DocumentResponse.model_validate(doc) if hasattr(DocumentResponse, 'model_validate') else DocumentResponse.from_orm(doc)
            for doc in documents
        ]
        
        return DocumentListResponse(
            items=document_list,
            total=total_count,
            page=page,
            page_size=page_size
        )
    
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.patch("/documents/{document_id}/metadata", response_model=DocumentResponse)
async def update_document_metadata(
    document_id: int,
    metadata: Dict[str, Any],
    document_service: DocumentProcessingService = Depends(get_document_service)
):
    """
    Update document metadata.
    
    Args:
        document_id: The document ID
        metadata: Metadata fields to update
        document_service: Document processing service from dependency injection
        
    Returns:
        Updated document data
    """
    try:
        # Update document metadata
        document = document_service.update_document_metadata(document_id, metadata)
        
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID '{document_id}' not found"
            )
        
        # Convert document to response model
        return DocumentResponse.model_validate(document) if hasattr(DocumentResponse, 'model_validate') else DocumentResponse.from_orm(document)
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logger.error(f"Error updating document metadata: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document metadata: {str(e)}"
        )


@router.get("/stats/pipeline", response_model=Dict[str, Any])
async def get_pipeline_stats(
    document_service: DocumentProcessingService = Depends(get_document_service)
):
    """
    Get document processing pipeline statistics.
    
    Args:
        document_service: Document processing service from dependency injection
        
    Returns:
        Pipeline statistics
    """
    try:
        return document_service.get_pipeline_stats()
    except Exception as e:
        logger.error(f"Error getting pipeline stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pipeline stats: {str(e)}"
        )


@router.get("/stats/cache", response_model=Dict[str, Any])
async def get_cache_stats(
    document_service: DocumentProcessingService = Depends(get_document_service)
):
    """
    Get document cache statistics.
    
    Args:
        document_service: Document processing service from dependency injection
        
    Returns:
        Cache statistics
    """
    try:
        return document_service.get_cache_stats()
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache stats: {str(e)}"
        )


@router.post("/cache/clear", response_model=Dict[str, bool])
async def clear_document_cache(
    document_service: DocumentProcessingService = Depends(get_document_service)
):
    """
    Clear the document cache.
    
    Args:
        document_service: Document processing service from dependency injection
        
    Returns:
        Success status
    """
    try:
        success = document_service.clear_document_cache()
        return {"success": success}
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        ) 