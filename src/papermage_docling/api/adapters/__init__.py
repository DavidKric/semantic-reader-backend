"""
Document format adapters for the semantic reader.

This package provides adapters for converting between different document formats
supported by the semantic reader. It uses the adapter pattern to decouple the 
semantic reader from the details of specific document formats.

Note: This is an internal implementation detail. For document operations,
use the DocumentGateway interface in papermage_docling.api.gateway instead.
"""

from papermage_docling.api.adapters.base import (
    BaseAdapter,
    FormatVersionInfo,
    AdapterRegistry
)
from papermage_docling.api.adapters.pdf import PdfToPapermageAdapter
from papermage_docling.api.adapters.factory import (
    get_adapter,
    register_adapter,
    list_supported_formats,
    convert_document
)

__all__ = [
    # Base classes
    'BaseAdapter',
    'FormatVersionInfo',
    'AdapterRegistry',
    
    # Concrete adapters
    'PdfToPapermageAdapter',
    
    # Factory functions
    'get_adapter',
    'register_adapter',
    'list_supported_formats',
    'convert_document',
] 