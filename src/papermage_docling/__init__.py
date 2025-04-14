"""
PaperMage Docling - PDF parsing and document processing library

This package provides document parsing and processing capabilities
using Docling's core functionality, with API compatibility with PaperMage.
"""

__version__ = "0.1.0"

# Import and expose key components for easy access
from papermage_docling.parsers import DoclingPdfParser
from papermage_docling.recipe import CoreRecipe

# Import adapters for format conversion
from papermage_docling.adapters import PaperMageAdapter

# Import API components
from papermage_docling.api import gateway

__all__ = [
    "DoclingPdfParser",
    "CoreRecipe",
    "PaperMageAdapter",
    "gateway"
] 