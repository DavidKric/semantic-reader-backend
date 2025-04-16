"""
PaperMage Docling - PDF parsing and document processing library

This package provides document parsing and processing capabilities
using Docling's core functionality with direct integration to Docling's
official API for PDF and document processing.
"""

__version__ = "0.1.0"

# Import and expose key components for easy access
from papermage_docling.converter import convert_document

__all__ = [
    "convert_document",
] 