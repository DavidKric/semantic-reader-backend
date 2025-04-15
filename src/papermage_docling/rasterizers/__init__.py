"""
Legacy rasterizers compatibility layer.

This module provides stubs and compatibility imports for code that might
still reference the old rasterizer classes, which have been removed in favor
of direct Docling integration.

DEPRECATED: These are placeholder compatibility classes that will be removed in a future version.
"""

import warnings
from typing import Any, Dict, List, Optional

# For compatibility with code that imports PdfRasterizer
class PdfRasterizer:
    """
    Legacy compatibility class for PDF rasterization.
    
    DEPRECATED: This class is maintained only for backward compatibility.
    Docling now handles PDF rasterization internally.
    """
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "PdfRasterizer is deprecated and will be removed in a future version. "
            "Docling now handles rasterization internally.",
            DeprecationWarning,
            stacklevel=2
        )
    
    def rasterize_page(self, *args, **kwargs):
        """Stub method for compatibility."""
        warnings.warn(
            "PdfRasterizer.rasterize_page is deprecated and will be removed in a future version. "
            "Docling now handles rasterization internally.",
            DeprecationWarning,
            stacklevel=2
        )
        raise NotImplementedError("Legacy rasterizer methods are no longer supported")
    
    def rasterize_pages(self, *args, **kwargs):
        """Stub method for compatibility."""
        warnings.warn(
            "PdfRasterizer.rasterize_pages is deprecated and will be removed in a future version. "
            "Docling now handles rasterization internally.",
            DeprecationWarning,
            stacklevel=2
        )
        raise NotImplementedError("Legacy rasterizer methods are no longer supported") 