"""
Analysis tools for understanding the PaperMage-Docling codebase.

This package provides utilities for analyzing the codebase structure,
document formats, and conversion points to guide refactoring and development.
"""

from .document_conversion_map import (
    create_conversion_map,
    DocumentConversionMap,
    ConversionPoint
)

__all__ = [
    'create_conversion_map',
    'DocumentConversionMap',
    'ConversionPoint'
] 