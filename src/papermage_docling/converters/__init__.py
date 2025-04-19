"""
Document conversion models and utilities.

This module provides the Pydantic models for document representation
and compatibility imports for the removed docling_to_papermage_converter.
"""

import warnings
from typing import Any, Dict, List, Optional

# Import document models
from .document import Box, Document, Entity, Span

__all__ = ["Box", "Span", "Entity", "Document"]

# For compatibility with code that imports DoclingToPaperMageConverter
class DoclingToPaperMageConverter:
    """
    Legacy compatibility class for Docling to PaperMage conversion.
    
    DEPRECATED: This class is maintained only for backward compatibility.
    Use the new converter module instead.
    """
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "DoclingToPaperMageConverter is deprecated and will be removed in a future version. "
            "Use the new converter module instead.",
            DeprecationWarning,
            stacklevel=2
        )
    
    @staticmethod
    def convert_document(*args, **kwargs):
        """Stub method for compatibility."""
        warnings.warn(
            "DoclingToPaperMageConverter.convert_document is deprecated and will be removed in a future version. "
            "Use the new converter module instead.",
            DeprecationWarning,
            stacklevel=2
        )
        from papermage_docling.converter import convert_document
        return convert_document(*args, **kwargs) 