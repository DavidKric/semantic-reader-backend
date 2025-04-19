"""
Pydantic models for request/response validation.

This module defines the data models used for API request validation
and response serialization using Pydantic.
"""

import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, validator

# Health and Version Endpoints Models

class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = "ok"
    timestamp: datetime = Field(default_factory=datetime.now)

class VersionResponse(BaseModel):
    """Response model for version endpoint."""
    version: str
    api_version: str
    commit: Optional[str] = None

# Document Processing Options Models

class FileValidationParams(BaseModel):
    """Parameters for file validation."""
    allowed_extensions: List[str] = ["pdf"]
    max_size_bytes: int = 10 * 1024 * 1024  # 10MB default
    max_page_count: int = 100
    
    @validator("max_size_bytes")
    def validate_max_size(cls, v):
        """Validate maximum file size."""
        if v <= 0:
            raise ValueError("File size limit must be positive")
        return v

class ConversionOptions(BaseModel):
    """Options for document conversion."""
    perform_ocr: bool = False
    ocr_language: str = "eng"
    detect_rtl: bool = True
    extract_tables: bool = True
    extract_figures: bool = True
    extract_equations: bool = False
    extract_sections: bool = True
    confidence_threshold: float = Field(0.8, ge=0.0, le=1.0)
    timeout_seconds: int = Field(30, ge=5, le=300)
    
    @validator('ocr_language')
    def validate_language_code(cls, v):
        """Validate OCR language code."""
        if not re.match(r'^[a-z]{3}$', v):
            raise ValueError("OCR language must be a 3-letter ISO language code")
        return v
    
    class Config:
        """Configuration for model examples."""
        json_schema_extra = {
            "example": {
                "perform_ocr": True,
                "ocr_language": "eng",
                "detect_rtl": True,
                "extract_tables": True,
                "extract_figures": True
            }
        }

# URL-based Conversion Models

class ConvertURLRequest(BaseModel):
    """Request model for URL-based document conversion."""
    urls: List[str]
    options: Optional[ConversionOptions] = Field(default_factory=ConversionOptions)
    
    @validator('urls')
    def validate_urls(cls, urls):
        """Validate URLs."""
        if not urls:
            raise ValueError("At least one URL must be provided")
        for url in urls:
            if not url.startswith(('http://', 'https://')):
                raise ValueError(f"Invalid URL format: {url}")
        return urls
    
    class Config:
        """Configuration for model examples."""
        json_schema_extra = {
            "example": {
                "urls": ["https://example.com/document.pdf"],
                "options": {
                    "perform_ocr": True,
                    "ocr_language": "eng",
                    "extract_tables": True
                }
            }
        }

# Response Models

class ProcessingMetadata(BaseModel):
    """Metadata about document processing."""
    processing_time_ms: int
    page_count: int
    ocr_performed: bool
    ocr_language: Optional[str] = None
    extraction_date: datetime = Field(default_factory=datetime.now)
    docling_version: str = "0.1.0"

class PageSchema(BaseModel):
    """Schema for document page data."""
    page_number: int
    width: float
    height: float
    rotation: float = 0.0

class DocumentJSONSchema(BaseModel):
    """Schema for document JSON output."""
    symbols: str  # Full text content
    metadata: Dict[str, Any] = Field(default_factory=dict)
    pages: List[PageSchema] = Field(default_factory=list)

class DocumentResult(BaseModel):
    """Result of document processing."""
    status: Literal["success", "failed"]
    document: Optional[DocumentJSONSchema] = None
    error: Optional[str] = None
    filename: Optional[str] = None
    url: Optional[str] = None

class ConvertResponse(BaseModel):
    """Response model for document conversion."""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: Literal["processing", "completed", "failed"]
    results: Optional[List[DocumentResult]] = None
    
    class Config:
        """Configuration for model examples."""
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "results": [
                    {
                        "status": "success",
                        "document": {
                            "symbols": "Example document text...",
                            "metadata": {"title": "Example Document"},
                            "pages": [{"page_number": 1, "width": 612, "height": 792, "rotation": 0}]
                        },
                        "filename": "example.pdf"
                    }
                ]
            }
        }

class JobStatusResponse(BaseModel):
    """Response model for job status check."""
    job_id: str
    status: Literal["processing", "completed", "failed"]
    created_at: str
    updated_at: Optional[str] = None
    results: Optional[List[DocumentResult]] = None

# Error Response Models

class ErrorLocation(BaseModel):
    """Location information for an error."""
    file: Optional[str] = None
    page: Optional[int] = None
    component: Optional[str] = None

class ErrorDetail(BaseModel):
    """Detailed error information."""
    loc: Optional[List[Union[str, int]]] = None
    msg: str
    type: str

class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: Union[List[ErrorDetail], str]
    status_code: int = 400

class DetailedErrorResponse(BaseModel):
    """Detailed error response with context."""
    error_code: str
    message: str
    location: Optional[ErrorLocation] = None
    details: Optional[Dict[str, Any]] = None
    traceback: Optional[str] = None
    
    class Config:
        """Configuration for model examples."""
        json_schema_extra = {
            "example": {
                "error_code": "PARSING_ERROR",
                "message": "Failed to parse PDF document",
                "location": {"file": "document.pdf", "page": 2},
                "details": {"reason": "Corrupted PDF structure"}
            }
        } 