"""
PaperMage API for document processing.

This module provides compatibility with the PaperMage API format while using
Docling directly for document processing.
"""

import logging
from typing import Any, Dict, List, Optional

from papermage_docling.converter import convert_document

logger = logging.getLogger(__name__)

def process_document(
    document: Any,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process a document using Docling and return it in PaperMage JSON format.
    
    Args:
        document: The document to process (file path, bytes, or file-like object)
        options: Processing options
            - enable_ocr: Whether to enable OCR
            - ocr_language: Language for OCR
            - detect_tables: Whether to detect tables
            - detect_figures: Whether to detect figures
    
    Returns:
        Dict: Document in PaperMage JSON format
    """
    if options is None:
        options = {}
    
    # Convert using the new unified converter
    result = convert_document(document, options=options)
    
    # Add PaperMage versioning wrapper (for compatibility)
    return {
        "version": "1.0",
        "document": result
    }

def get_supported_formats() -> List[str]:
    """
    Get list of supported document formats.
    
    Returns:
        List[str]: Supported formats
    """
    # Docling supports PDF, DOCX, etc., but we'll start with PDF for compatibility
    return ["pdf"]

# For compatibility with code that expects the old PaperMage classes
class PaperMageManager:
    """
    Compatibility class for code that expects the old PaperMage API.
    This provides the same interface but uses Docling directly under the hood.
    """
    
    @staticmethod
    def process_document(document: Any, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a document using Docling and return it in PaperMage format.
        
        Args:
            document: The document to process
            options: Processing options
        
        Returns:
            Dict: Document in PaperMage format
        """
        return process_document(document, options)
    
    @staticmethod
    def get_supported_formats() -> List[str]:
        """
        Get list of supported document formats.
        
        Returns:
            List[str]: Supported formats
        """
        return get_supported_formats()

# Create a singleton instance for code that expects it
papermage = PaperMageManager() 