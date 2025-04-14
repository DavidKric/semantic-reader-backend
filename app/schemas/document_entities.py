"""
Pydantic schemas for document entities.

These schemas define the data structures for document entities in API requests and responses.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.schemas.base import BaseSchema


class BoundingBox(BaseSchema):
    """Bounding box for document entities."""
    
    x0: float = Field(..., description="Left coordinate")
    y0: float = Field(..., description="Bottom coordinate")
    x1: float = Field(..., description="Right coordinate")
    y1: float = Field(..., description="Top coordinate")
    
    @property
    def width(self) -> float:
        """Calculate width of the box."""
        return self.x1 - self.x0
    
    @property
    def height(self) -> float:
        """Calculate height of the box."""
        return self.y1 - self.y0


class TextBlock(BaseSchema):
    """Base schema for text blocks in documents."""
    
    id: Optional[str] = Field(None, description="Unique identifier")
    text: str = Field(..., description="Text content")
    bbox: Optional[BoundingBox] = Field(None, description="Bounding box")
    page_number: Optional[int] = Field(None, description="Page number")
    is_rtl: Optional[bool] = Field(None, description="Whether text is right-to-left")
    language: Optional[str] = Field(None, description="Language code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "block1",
                "text": "Example text content",
                "bbox": {
                    "x0": 50.0,
                    "y0": 100.0,
                    "x1": 300.0,
                    "y1": 120.0
                },
                "page_number": 1,
                "is_rtl": False,
                "language": "en"
            }
        }


class Word(TextBlock):
    """Schema for word entities."""
    
    font: Optional[str] = Field(None, description="Font name")
    font_size: Optional[float] = Field(None, description="Font size")
    is_bold: Optional[bool] = Field(None, description="Whether text is bold")
    is_italic: Optional[bool] = Field(None, description="Whether text is italic")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "word1",
                "text": "Example",
                "bbox": {
                    "x0": 50.0,
                    "y0": 100.0,
                    "x1": 100.0,
                    "y1": 120.0
                },
                "page_number": 1,
                "font": "Times New Roman",
                "font_size": 12.0,
                "is_bold": False,
                "is_italic": False
            }
        }


class Line(TextBlock):
    """Schema for line entities."""
    
    words: Optional[List[Word]] = Field(None, description="Words in the line")
    line_number: Optional[int] = Field(None, description="Line number in paragraph")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "line1",
                "text": "Example line of text",
                "bbox": {
                    "x0": 50.0,
                    "y0": 100.0,
                    "x1": 300.0,
                    "y1": 120.0
                },
                "page_number": 1,
                "line_number": 1
            }
        }


class ParagraphSchema(TextBlock):
    """Schema for paragraph entities."""
    
    paragraph_type: Optional[str] = Field(None, description="Paragraph type (normal, heading, list, etc.)")
    lines: Optional[List[Line]] = Field(None, description="Lines in the paragraph")
    order: Optional[int] = Field(None, description="Order in document/page")
    section_id: Optional[str] = Field(None, description="ID of parent section")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "para1",
                "text": "Example paragraph with multiple lines of text. This is a second sentence.",
                "bbox": {
                    "x0": 50.0,
                    "y0": 100.0,
                    "x1": 500.0,
                    "y1": 140.0
                },
                "page_number": 1,
                "paragraph_type": "normal",
                "order": 1,
                "section_id": "section1"
            }
        }


class SectionSchema(BaseSchema):
    """Schema for section entities."""
    
    id: Optional[str] = Field(None, description="Unique identifier")
    title: Optional[str] = Field(None, description="Section title")
    text: Optional[str] = Field(None, description="Section text")
    level: int = Field(1, description="Section level/depth (1 = top level)")
    order: int = Field(..., description="Order in document")
    start_page: Optional[int] = Field(None, description="Start page number")
    end_page: Optional[int] = Field(None, description="End page number")
    parent_id: Optional[str] = Field(None, description="ID of parent section")
    paragraphs: Optional[List[ParagraphSchema]] = Field(None, description="Paragraphs in the section")
    children: Optional[List["SectionSchema"]] = Field(None, description="Child sections")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "section1",
                "title": "Introduction",
                "level": 1,
                "order": 1,
                "start_page": 1,
                "end_page": 2
            }
        }


class FigureSchema(BaseSchema):
    """Schema for figure entities."""
    
    id: Optional[str] = Field(None, description="Unique identifier")
    caption: Optional[str] = Field(None, description="Figure caption")
    figure_number: Optional[str] = Field(None, description="Figure number (e.g., 'Figure 1.2')")
    page_number: int = Field(..., description="Page number")
    order: int = Field(..., description="Order in document/page")
    bbox: Optional[BoundingBox] = Field(None, description="Bounding box")
    figure_type: Optional[str] = Field(None, description="Figure type (image, chart, diagram, etc.)")
    image_path: Optional[str] = Field(None, description="Path to image file")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "figure1",
                "caption": "Example figure caption",
                "figure_number": "Figure 1.2",
                "page_number": 1,
                "order": 1,
                "bbox": {
                    "x0": 100.0,
                    "y0": 200.0,
                    "x1": 400.0,
                    "y1": 350.0
                },
                "figure_type": "image"
            }
        }


class TableSchema(BaseSchema):
    """Schema for table entities."""
    
    id: Optional[str] = Field(None, description="Unique identifier")
    caption: Optional[str] = Field(None, description="Table caption")
    table_number: Optional[str] = Field(None, description="Table number (e.g., 'Table 2.1')")
    page_number: int = Field(..., description="Page number")
    order: int = Field(..., description="Order in document/page")
    bbox: Optional[BoundingBox] = Field(None, description="Bounding box")
    rows: Optional[int] = Field(None, description="Number of rows")
    columns: Optional[int] = Field(None, description="Number of columns")
    data: Optional[List[List[Any]]] = Field(None, description="Table data as 2D array")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "table1",
                "caption": "Example table caption",
                "table_number": "Table 2.1",
                "page_number": 2,
                "order": 1,
                "bbox": {
                    "x0": 100.0,
                    "y0": 200.0,
                    "x1": 500.0,
                    "y1": 300.0
                },
                "rows": 3,
                "columns": 4
            }
        }


class PageSchema(BaseSchema):
    """Schema for page entities."""
    
    id: Optional[str] = Field(None, description="Unique identifier")
    page_number: int = Field(..., description="Page number")
    width: Optional[float] = Field(None, description="Page width")
    height: Optional[float] = Field(None, description="Page height")
    rotation: Optional[int] = Field(0, description="Page rotation in degrees")
    page_type: Optional[str] = Field(None, description="Page type (title, toc, content, references, etc.)")
    paragraphs: Optional[List[ParagraphSchema]] = Field(None, description="Paragraphs on the page")
    figures: Optional[List[FigureSchema]] = Field(None, description="Figures on the page")
    tables: Optional[List[TableSchema]] = Field(None, description="Tables on the page")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "page1",
                "page_number": 1,
                "width": 612.0,
                "height": 792.0,
                "rotation": 0,
                "page_type": "content"
            }
        }


class DocumentSchema(BaseSchema):
    """Schema for document entities."""
    
    id: Optional[str] = Field(None, description="Unique identifier")
    title: Optional[str] = Field(None, description="Document title")
    filename: Optional[str] = Field(None, description="Original filename")
    file_type: str = Field(..., description="File type (pdf, docx, etc.)")
    num_pages: Optional[int] = Field(None, description="Number of pages")
    language: Optional[str] = Field(None, description="Primary document language")
    has_rtl: Optional[bool] = Field(False, description="Whether document contains right-to-left text")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    storage_id: Optional[str] = Field(None, description="ID in document storage")
    ocr_applied: Optional[bool] = Field(False, description="Whether OCR was applied")
    processing_status: Optional[str] = Field("pending", description="Processing status")
    
    # Optional nested entities
    pages: Optional[List[PageSchema]] = Field(None, description="Document pages")
    sections: Optional[List[SectionSchema]] = Field(None, description="Document sections")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc1",
                "title": "Example Document",
                "filename": "example.pdf",
                "file_type": "pdf",
                "num_pages": 10,
                "language": "en",
                "has_rtl": False,
                "created_at": "2023-04-15T12:00:00Z",
                "updated_at": "2023-04-15T12:05:00Z",
                "storage_id": "abc123",
                "ocr_applied": False,
                "processing_status": "completed"
            }
        }


# Document analysis results
class StructureAnalysisResult(BaseSchema):
    """Schema for structure analysis results."""
    
    sections_count: int = Field(..., description="Number of sections")
    paragraphs_count: int = Field(..., description="Number of paragraphs")
    structure_hierarchy: Any = Field(..., description="Document structure hierarchy")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sections_count": 5,
                "paragraphs_count": 25,
                "structure_hierarchy": {
                    "title": "Document Title",
                    "sections": [
                        {"title": "Introduction", "level": 1, "order": 1},
                        {"title": "Background", "level": 1, "order": 2}
                    ]
                }
            }
        }


class LanguageAnalysisResult(BaseSchema):
    """Schema for language analysis results."""
    
    document_language: str = Field(..., description="Primary document language code")
    language_name: str = Field(..., description="Language name")
    confidence: float = Field(..., description="Detection confidence score")
    is_rtl: bool = Field(..., description="Whether language is right-to-left")
    additional_languages: List[Dict[str, Any]] = Field([], description="Additional languages detected")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_language": "en",
                "language_name": "English",
                "confidence": 0.98,
                "is_rtl": False,
                "additional_languages": [
                    {"language": "fr", "language_name": "French", "confidence": 0.02}
                ]
            }
        }


class TableAnalysisResult(BaseSchema):
    """Schema for table analysis results."""
    
    tables_count: int = Field(..., description="Number of tables detected")
    tables_by_page: Any = Field(..., description="Tables breakdown by page")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tables_count": 3,
                "tables_by_page": {
                    "1": 1,
                    "3": 2
                }
            }
        }


class FigureAnalysisResult(BaseSchema):
    """Schema for figure analysis results."""
    
    figures_count: int = Field(..., description="Number of figures detected")
    figures_by_page: Any = Field(..., description="Figures breakdown by page")
    
    class Config:
        json_schema_extra = {
            "example": {
                "figures_count": 4,
                "figures_by_page": {
                    "2": 1,
                    "4": 2,
                    "5": 1
                }
            }
        } 