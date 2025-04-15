"""
Parser modules for extracting information from PDFs.
"""

from .docling_pdf_parser import DoclingPdfParser

__all__ = ["DoclingPdfParser"]

"""
Legacy parsers compatibility layer.

This module provides stubs and compatibility imports for code that might
still reference the old parser classes, which have been removed in favor
of direct Docling integration.

DEPRECATED: These are placeholder compatibility classes that will be removed in a future version.
"""

import warnings
from typing import Any, Dict, List, Optional

# For compatibility with code that imports DoclingPdfParser
class DoclingPdfParser:
    """
    Legacy compatibility class for PDF parsing.
    
    DEPRECATED: This class is maintained only for backward compatibility.
    Docling now handles PDF parsing internally.
    """
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "DoclingPdfParser is deprecated and will be removed in a future version. "
            "Use the new converter module instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.options = kwargs
    
    def parse(self, document, *args, **kwargs):
        """
        Legacy compatibility method for parsing PDFs.
        
        Args:
            document: The document to parse
            *args: Additional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            The parsed document
        """
        warnings.warn(
            "DoclingPdfParser.parse is deprecated and will be removed in a future version. "
            "Use the new converter module instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        from papermage_docling.converter import convert_document
        options = self.options.copy()
        options.update(kwargs)
        
        return convert_document(document, options=options) 