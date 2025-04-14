"""
Storage package for DoclingDocument persistence and caching.

This package provides interfaces and implementations for storing and 
retrieving DoclingDocument objects, with support for both file-based
and database storage as well as caching mechanisms.
"""

from papermage_docling.storage.interface import DocumentStorage
from papermage_docling.storage.file_storage import FileDocumentStorage
from papermage_docling.storage.cache import DocumentCache, LRUDocumentCache

__all__ = [
    "DocumentStorage",
    "FileDocumentStorage",
    "DocumentCache",
    "LRUDocumentCache"
] 