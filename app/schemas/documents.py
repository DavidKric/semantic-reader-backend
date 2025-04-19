"""
Document-related schemas for request/response validation.

This module contains Pydantic models for document processing endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.base import BaseSchema
from app.schemas.document_entities import PageSchema, SectionSchema


class DocumentProcessingOptions(BaseModel):
    """Options for document processing."""
    page_range: Optional[List[int]] = None
    detect_rtl: bool = True
    ocr_enabled: bool = False
    ocr_language: str = "eng"
    extract_tables: bool = True
    extract_figures: bool = True
    extract_sections: bool = True
    return_papermage: bool = False
    
    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "page_range": [1, 2, 3],
                "detect_rtl": True,
                "ocr_enabled": False,
                "ocr_language": "eng",
                "extract_tables": True,
                "extract_figures": True,
                "extract_sections": True,
                "return_papermage": False
            }
        }
    )


class DocumentMetadata(BaseModel):
    """Document metadata."""
    language: Optional[str] = None
    is_rtl: Optional[bool] = False
    ocr_applied: Optional[bool] = False
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )


class DocumentResponse(BaseSchema):
    """Document response."""
    id: int
    title: Optional[str] = None
    filename: Optional[str] = None
    file_type: str
    language: Optional[str] = None
    has_rtl: bool = False
    storage_id: Optional[str] = None
    storage_path: Optional[str] = None
    processing_status: str
    is_processed: bool
    created_at: datetime
    updated_at: datetime
    num_pages: Optional[int] = None
    word_count: Optional[int] = None
    doc_metadata: Optional[Dict[str, Any]] = None
    pages: Optional[List[PageSchema]] = None
    sections: Optional[List[SectionSchema]] = None
    
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )


class DocumentListResponse(BaseSchema):
    """Response containing a list of documents."""
    items: List[DocumentResponse]
    total: int
    page: int
    page_size: int


class ProcessDocumentRequest(BaseModel):
    """Request for document processing."""
    file_path: str
    options: Optional[DocumentProcessingOptions] = None


class PaperMageResponse(BaseSchema):
    """PaperMage format document response."""
    document_id: Optional[str] = None
    status: str
    data: Dict[str, Any]


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