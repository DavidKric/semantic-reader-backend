"""
Pydantic schemas for the application.

This package contains Pydantic models that are used for request/response validation,
serialization/deserialization, and OpenAPI documentation.
"""

# Import schemas here to make them available from the schemas package
from app.schemas.base import BaseSchema, PaginationParams, PaginatedResponse
from app.schemas.health import HealthResponse, DetailedHealthResponse, VersionResponse
from app.schemas.documents import (
    DocumentResponse,
    PaperMageResponse,
    DocumentListResponse,
    ProcessDocumentRequest,
    DocumentProcessingOptions
)
from app.schemas.document_entities import (
    BoundingBox,
    TextBlock,
    Word,
    Line,
    ParagraphSchema,
    SectionSchema,
    FigureSchema,
    TableSchema,
    PageSchema,
    DocumentSchema,
    StructureAnalysisResult,
    LanguageAnalysisResult,
    TableAnalysisResult,
    FigureAnalysisResult
)

__all__ = [
    # Base schemas
    "BaseSchema",
    "PaginationParams",
    "PaginatedResponse",
    
    # Health schemas
    "HealthResponse",
    "DetailedHealthResponse", 
    "VersionResponse",
    
    # Document schemas
    "DocumentResponse",
    "PaperMageResponse",
    "DocumentListResponse",
    "ProcessDocumentRequest",
    "DocumentProcessingOptions",
    
    # Document entity schemas
    "BoundingBox",
    "TextBlock",
    "Word",
    "Line",
    "ParagraphSchema",
    "SectionSchema",
    "FigureSchema",
    "TableSchema",
    "PageSchema",
    "DocumentSchema",
    
    # Analysis result schemas
    "StructureAnalysisResult",
    "LanguageAnalysisResult",
    "TableAnalysisResult",
    "FigureAnalysisResult"
] 