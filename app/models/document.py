"""
Document models for the Semantic Reader backend.

These models represent document entities such as documents, pages, sections,
paragraphs, and text blocks in the database and for API responses.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Document(BaseModel):
    """Document database model."""
    
    __tablename__ = "documents"
    
    # Basic metadata
    title = Column(String(255), nullable=True, index=True)
    filename = Column(String(255), nullable=True)
    file_type = Column(String(32), nullable=False)  # pdf, docx, etc.
    
    # Content statistics
    num_pages = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    
    # Language and direction
    language = Column(String(32), nullable=True)
    has_rtl = Column(Boolean, default=False)
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(32), default="pending")  # pending, processing, completed, failed
    
    # Storage
    storage_path = Column(String(255), nullable=True)
    storage_id = Column(String(64), nullable=True, index=True)  # ID in document storage
    
    # Metadata and extraction flags
    doc_metadata = Column(JSON, nullable=True)
    ocr_applied = Column(Boolean, default=False)
    
    # Relationships
    pages = relationship("Page", back_populates="document", cascade="all, delete-orphan")
    sections = relationship("Section", back_populates="document", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary."""
        result = super().to_dict()
        
        # Add related objects if needed
        # (consider using a depth parameter to control recursion)
        
        return result


class Page(BaseModel):
    """Page database model."""
    
    __tablename__ = "pages"
    
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    width = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    rotation = Column(Integer, default=0)  # Page rotation in degrees
    
    # Content statistics
    word_count = Column(Integer, nullable=True)
    
    # Page type classification
    page_type = Column(String(32), nullable=True)  # title, toc, content, references, etc.
    
    # Relationships
    document = relationship("Document", back_populates="pages")
    paragraphs = relationship("Paragraph", back_populates="page", cascade="all, delete-orphan")
    
    # Metadata
    doc_metadata = Column(JSON, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert page to dictionary."""
        result = super().to_dict()
        
        # Add related objects if needed
        
        return result


class Section(BaseModel):
    """Section database model."""
    
    __tablename__ = "sections"
    
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    title = Column(String(255), nullable=True)
    level = Column(Integer, default=1)  # Section level/depth (1 = top level)
    order = Column(Integer, nullable=False)  # Order in document
    
    # Section start and end
    start_page = Column(Integer, nullable=True)
    end_page = Column(Integer, nullable=True)
    
    # Content statistics
    word_count = Column(Integer, nullable=True)
    
    # Parent section for hierarchy
    parent_id = Column(Integer, ForeignKey("sections.id"), nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="sections")
    paragraphs = relationship("Paragraph", back_populates="section", cascade="all, delete-orphan")
    children = relationship("Section", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("Section", back_populates="children", remote_side="Section.id")
    
    # Section text (optional)
    text = Column(Text, nullable=True)
    
    # Metadata
    doc_metadata = Column(JSON, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert section to dictionary."""
        result = super().to_dict()
        
        # Add related objects if needed
        
        return result


class Paragraph(BaseModel):
    """Paragraph database model."""
    
    __tablename__ = "paragraphs"
    
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=True)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=True)
    
    # Position in document
    page_number = Column(Integer, nullable=True)
    order = Column(Integer, nullable=False)  # Order in document/page
    
    # Text content
    text = Column(Text, nullable=True)
    
    # Content metadata
    word_count = Column(Integer, nullable=True)
    is_rtl = Column(Boolean, default=False)
    language = Column(String(32), nullable=True)
    
    # Bounding box (PDF coordinates)
    x0 = Column(Float, nullable=True)
    y0 = Column(Float, nullable=True)
    x1 = Column(Float, nullable=True)
    y1 = Column(Float, nullable=True)
    
    # Paragraph type classification
    paragraph_type = Column(String(32), nullable=True)  # normal, heading, list, etc.
    
    # Relationships
    document = relationship("Document")
    page = relationship("Page", back_populates="paragraphs")
    section = relationship("Section", back_populates="paragraphs")
    
    # Metadata
    doc_metadata = Column(JSON, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert paragraph to dictionary."""
        result = super().to_dict()
        
        # Add related objects if needed
        
        return result


class Figure(BaseModel):
    """Figure database model."""
    
    __tablename__ = "figures"
    
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=True)
    
    # Position in document
    page_number = Column(Integer, nullable=True)
    order = Column(Integer, nullable=False)  # Order in document/page
    
    # Figure information
    caption = Column(Text, nullable=True)
    figure_number = Column(String(32), nullable=True)  # E.g., "Figure 1.2"
    
    # Bounding box (PDF coordinates)
    x0 = Column(Float, nullable=True)
    y0 = Column(Float, nullable=True)
    x1 = Column(Float, nullable=True)
    y1 = Column(Float, nullable=True)
    
    # Figure type
    figure_type = Column(String(32), nullable=True)  # image, chart, diagram, etc.
    
    # Optional image storage
    image_path = Column(String(255), nullable=True)
    
    # Relationships
    document = relationship("Document")
    page = relationship("Page")
    
    # Metadata
    doc_metadata = Column(JSON, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert figure to dictionary."""
        result = super().to_dict()
        
        # Add related objects if needed
        
        return result


class Table(BaseModel):
    """Table database model."""
    
    __tablename__ = "tables"
    
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=True)
    
    # Position in document
    page_number = Column(Integer, nullable=True)
    order = Column(Integer, nullable=False)  # Order in document/page
    
    # Table information
    caption = Column(Text, nullable=True)
    table_number = Column(String(32), nullable=True)  # E.g., "Table 2.1"
    
    # Table structure
    rows = Column(Integer, nullable=True)
    columns = Column(Integer, nullable=True)
    
    # Bounding box (PDF coordinates)
    x0 = Column(Float, nullable=True)
    y0 = Column(Float, nullable=True)
    x1 = Column(Float, nullable=True)
    y1 = Column(Float, nullable=True)
    
    # Table data (can be stored as JSON or in related table cell records)
    data = Column(JSON, nullable=True)
    
    # Relationships
    document = relationship("Document")
    page = relationship("Page")
    
    # Metadata
    doc_metadata = Column(JSON, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert table to dictionary."""
        result = super().to_dict()
        
        # Add related objects if needed
        
        return result 