"""
Document-related schemas for request/response validation.

This module contains Pydantic models for document processing endpoints.
"""

from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema


class DocumentProcessingOptions(BaseModel):
    """Options for document processing."""
    page_range: Optional[List[int]] = None
    detect_rtl: bool = True
    ocr_enabled: bool = False
    ocr_language: str = "eng"


class ProcessDocumentRequest(BaseModel):
    """Request model for document processing."""
    options: Optional[DocumentProcessingOptions] = None
    save_document: bool = True
    output_format: str = "docling"

    class Config:
        json_schema_extra = {
            "example": {
                "options": {
                    "page_range": [1, 2, 3],
                    "detect_rtl": True,
                    "ocr_enabled": False
                },
                "save_document": True,
                "output_format": "docling"
            }
        }


class DocumentResponse(BaseSchema):
    """Response model for document processing endpoints."""
    status: str = "success"
    document_id: Optional[str] = None
    data: Dict[str, Any]


class PaperMageResponse(BaseSchema):
    """Response model for PaperMage format."""
    status: str = "success"
    document_id: Optional[str] = None
    data: Dict[str, Any]


class DocumentMeta(BaseModel):
    """Document metadata."""
    id: str
    filename: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    file_type: Optional[str] = None
    num_pages: Optional[int] = None
    language: Optional[str] = None
    has_rtl: Optional[bool] = None


class DocumentListResponse(BaseSchema):
    """Response model for listing documents."""
    status: str = "success"
    count: int
    documents: List[DocumentMeta]


class DocumentAnalysisRequest(BaseModel):
    """Request model for document analysis."""
    document_id: str
    analysis_type: str
    parameters: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "abc123",
                "analysis_type": "language_detection",
                "parameters": {"min_confidence": 0.7}
            }
        }


class DocumentAnalysisResponse(BaseSchema):
    """Response model for document analysis."""
    status: str = "success"
    document_id: str
    analysis_type: str
    results: Dict[str, Any] 