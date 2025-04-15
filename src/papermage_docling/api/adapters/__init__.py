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

"""
Legacy adapter compatibility layer.

This module provides stubs and compatibility imports for code that might
still reference the old adapter classes, which have been removed in favor
of direct Docling integration.

DEPRECATED: These are placeholder compatibility classes that will be removed in a future version.
"""

import warnings
from typing import Any, Dict, List, Optional, Union

# For compatibility with code that imports FormatVersionInfo
class FormatVersionInfo:
    """
    Legacy compatibility class for format version information.
    
    DEPRECATED: This class is maintained only for backward compatibility.
    """
    def __init__(self, format_name: str, version: str, description: str = ""):
        self.format_name = format_name
        self.version = version
        self.description = description
        
        warnings.warn(
            "FormatVersionInfo is deprecated and will be removed in a future version. "
            "Use the new converter module instead.",
            DeprecationWarning,
            stacklevel=2
        )

# For compatibility with code that imports BaseAdapter
class BaseAdapter:
    """
    Legacy compatibility class for the base adapter.
    
    DEPRECATED: This class is maintained only for backward compatibility.
    """
    def __init__(self):
        warnings.warn(
            "BaseAdapter is deprecated and will be removed in a future version. "
            "Use the new converter module instead.",
            DeprecationWarning,
            stacklevel=2
        )
    
    def convert(self, data: Any, **kwargs) -> Any:
        """Stub method for compatibility."""
        raise NotImplementedError("Legacy adapter methods are no longer supported")

# For compatibility with code that imports from factory
def get_adapter(*args, **kwargs):
    """
    Legacy compatibility function for getting an adapter.
    
    DEPRECATED: This function is maintained only for backward compatibility.
    """
    warnings.warn(
        "get_adapter is deprecated and will be removed in a future version. "
        "Use the new converter module instead.",
        DeprecationWarning,
        stacklevel=2
    )
    raise NotImplementedError("Legacy adapter methods are no longer supported")

def register_adapter(*args, **kwargs):
    """
    Legacy compatibility function for registering an adapter.
    
    DEPRECATED: This function is maintained only for backward compatibility.
    """
    warnings.warn(
        "register_adapter is deprecated and will be removed in a future version. "
        "Use the new converter module instead.",
        DeprecationWarning,
        stacklevel=2
    )

def list_supported_formats(*args, **kwargs):
    """
    Legacy compatibility function for listing supported formats.
    
    DEPRECATED: This function is maintained only for backward compatibility.
    """
    warnings.warn(
        "list_supported_formats is deprecated and will be removed in a future version. "
        "Use the new converter module instead.",
        DeprecationWarning,
        stacklevel=2
    )
    from papermage_docling.api.gateway import get_supported_formats
    return {"pdf": ["papermage"]} 