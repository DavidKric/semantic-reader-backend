"""
Document Gateway for the Semantic Reader API.

This module provides the gateway interface for document operations in the semantic reader,
using Docling directly for document processing.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from papermage_docling.converter import convert_document

logger = logging.getLogger(__name__)

def process_document(
    document: Any,
    options: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Process a document using Docling and return the result in PaperMage format.
    
    Args:
        document: The document to process (path, bytes, or file-like object)
        options: Options for document processing
            - enable_ocr: Whether to enable OCR (default: False)
            - ocr_language: Language for OCR (default: "eng")
            - detect_tables: Whether to detect tables (default: True)
            - detect_figures: Whether to detect figures (default: True)
        **kwargs: Additional parameters for the conversion process
            
    Returns:
        Dict[str, Any]: The processed document in PaperMage format
        
    Raises:
        ValueError: If document processing fails
    """
    if options is None:
        options = {}
    
    try:
        # Map options to converter options
        converter_options = {
            "detect_tables": options.get("detect_tables", True),
            "detect_figures": options.get("detect_figures", True),
            "enable_ocr": options.get("enable_ocr", False),
            "ocr_language": options.get("ocr_language", "eng"),
        }
        
        # Process using the new unified converter
        logger.info(f"Processing document with options: {converter_options}")
        result = convert_document(document, options=converter_options)
        
        return result
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise ValueError(f"Document processing failed: {e}") from e


def get_supported_formats() -> List[str]:
    """
    Get a list of supported document formats.
    
    Returns:
        List[str]: List of supported input formats (currently only PDF)
    """
    # Docling supports PDF, DOCX, etc., but we'll start with PDF for consistency
    return ["pdf"]


# Compatibility function for the old gateway API
def process_legacy(
    document: Any,
    source_format: str = "pdf",
    target_format: str = "papermage",
    **kwargs
) -> Any:
    """
    Legacy compatibility function that mimics the old convert method.
    
    Args:
        document: The document to convert
        source_format: Source format (ignored, always assumes PDF)
        target_format: Target format (ignored, always produces PaperMage JSON)
        **kwargs: Additional parameters passed to process_document
            
    Returns:
        The processed document in PaperMage format
    """
    # Extract adapter prefixed options
    adapter_options = {}
    for key, value in list(kwargs.items()):
        if key.startswith("adapter_"):
            real_key = key[8:]  # Remove "adapter_" prefix
            adapter_options[real_key] = value
            kwargs.pop(key)
    
    # Override options with adapter_options
    kwargs.update(adapter_options)
    
    # Process using the new unified converter
    return process_document(document, options=kwargs) 