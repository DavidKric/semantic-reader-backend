"""
PDF to Papermage document adapter implementation.

This module provides adapters for converting PDF documents to Papermage format.
"""

from typing import Any, Dict, Optional

from papermage_docling.api.adapters.base import BaseAdapter, FormatVersionInfo
from papermage_docling.parsers import DoclingPdfParser


class PdfToPapermageAdapter(BaseAdapter):
    """
    Adapter that converts PDF documents to Papermage format.
    
    This adapter uses the DoclingPdfParser to convert PDF documents into the
    Papermage document format used by the semantic reader.
    """
    
    def __init__(self):
        """Initialize the PDF to Papermage adapter."""
        self._source_format = FormatVersionInfo(format_name="pdf")
        self._target_format = FormatVersionInfo(
            format_name="papermage", 
            major_version=1, 
            minor_version=0
        )
    
    @property
    def source_format(self) -> FormatVersionInfo:
        """Get the source format (PDF) this adapter accepts."""
        return self._source_format
        
    @property
    def target_format(self) -> FormatVersionInfo:
        """Get the target format (Papermage) this adapter produces."""
        return self._target_format
        
    def convert(self, document: Any, **kwargs) -> Dict[str, Any]:
        """
        Convert a PDF document to Papermage format.
        
        Args:
            document: The PDF document to convert. This can be either a file path,
                     a file-like object, or binary PDF data.
            **kwargs: Additional parameters for the conversion. These will be
                     passed to the DoclingPdfParser.
                     
        Returns:
            Dict[str, Any]: The converted document in Papermage format
            
        Raises:
            ValueError: If the document format is invalid or conversion fails
        """
        # Extract specific parser parameters from kwargs
        parser_kwargs = {
            "enable_ocr": kwargs.pop("enable_ocr", False),
            "ocr_language": kwargs.pop("ocr_language", "eng"),
            "detect_rtl": kwargs.pop("detect_rtl", True),
            "min_line_height": kwargs.pop("min_line_height", None),
            "detect_tables": kwargs.pop("detect_tables", True),
            "detect_figures": kwargs.pop("detect_figures", True),
            "detect_equations": kwargs.pop("detect_equations", True),
            "detect_sections": kwargs.pop("detect_sections", True),
        }
        
        # If document is a path, open it and convert
        if isinstance(document, str):
            try:
                parser = DoclingPdfParser(**parser_kwargs)
                return parser.parse(document, **kwargs)
            except Exception as e:
                raise ValueError(f"Failed to convert PDF document: {str(e)}")
                
        # If document is bytes, convert directly
        elif isinstance(document, (bytes, bytearray)):
            try:
                parser = DoclingPdfParser(**parser_kwargs)
                return parser.parse_bytes(document, **kwargs)
            except Exception as e:
                raise ValueError(f"Failed to convert PDF document: {str(e)}")
                
        # Otherwise, assume file-like object
        else:
            try:
                content = document.read()
                parser = DoclingPdfParser(**parser_kwargs)
                return parser.parse_bytes(content, **kwargs)
            except Exception as e:
                raise ValueError(f"Failed to convert PDF document: {str(e)}") 