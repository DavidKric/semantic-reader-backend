"""
Converters module for transforming between document formats.
"""

from .document import Document, Entity, Span, Box
from .docling_to_papermage_converter import DoclingToPaperMageConverter

__all__ = [
    'Document', 
    'Entity', 
    'Span', 
    'Box',
    'DoclingToPaperMageConverter'
] 