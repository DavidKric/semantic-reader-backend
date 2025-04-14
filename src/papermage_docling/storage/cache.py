"""
Caching mechanisms for DoclingDocument objects.

This module provides caching implementations for DoclingDocument objects
to improve performance by avoiding repeated loading from storage.
"""

import time
import logging
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple, Callable
from functools import lru_cache
from collections import OrderedDict

# Import the DoclingDocument from docling_core
try:
    from docling_core.types import DoclingDocument
except ImportError:
    logging.warning("docling_core not found. DoclingDocument caching will not be available.")
    # Define a stub class for type hints only
    class DoclingDocument:
        pass

logger = logging.getLogger(__name__)


class DocumentCache(ABC):
    """
    Abstract base class for document caching implementations.
    
    This class defines the interface that all document cache implementations
    must follow, providing standard methods for caching DoclingDocument objects.
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[DoclingDocument]:
        """
        Get a document from the cache.
        
        Args:
            key: Cache key for the document
            
        Returns:
            The cached document, or None if not found
        """
        pass
    
    @abstractmethod
    def put(self, key: str, doc: DoclingDocument, ttl: Optional[int] = None) -> None:
        """
        Add a document to the cache.
        
        Args:
            key: Cache key for the document
            doc: The document to cache
            ttl: Optional time-to-live in seconds
        """
        pass
    
    @abstractmethod
    def remove(self, key: str) -> bool:
        """
        Remove a document from the cache.
        
        Args:
            key: Cache key for the document
            
        Returns:
            True if the document was removed, False if it wasn't in the cache
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all documents from the cache."""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary of cache statistics
        """
        pass


class LRUDocumentCache(DocumentCache):
    """
    LRU (Least Recently Used) cache for DoclingDocument objects.
    
    This class implements a thread-safe LRU cache for DoclingDocument objects,
    with optional TTL (time-to-live) support.
    """
    
    def __init__(self, max_size: int = 100, default_ttl: Optional[int] = None):
        """
        Initialize the LRU cache.
        
        Args:
            max_size: Maximum number of documents to cache
            default_ttl: Default time-to-live in seconds (None for no expiration)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()  # {key: (doc, expiry_time)}
        self.lock = threading.RLock()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0,
            "puts": 0
        }
        
        logger.info(f"Initialized LRUDocumentCache with max_size={max_size}, default_ttl={default_ttl}")
    
    def _evict_if_needed(self) -> None:
        """Evict the least recently used item if the cache is at capacity."""
        with self.lock:
            if len(self.cache) >= self.max_size:
                # Evict the LRU item (first in the OrderedDict)
                self.cache.popitem(last=False)
                self.stats["evictions"] += 1
    
    def _is_expired(self, expiry_time: Optional[float]) -> bool:
        """Check if an item has expired."""
        return expiry_time is not None and time.time() > expiry_time
    
    def get(self, key: str) -> Optional[DoclingDocument]:
        """
        Get a document from the cache.
        
        Args:
            key: Cache key for the document
            
        Returns:
            The cached document, or None if not found or expired
        """
        with self.lock:
            if key not in self.cache:
                self.stats["misses"] += 1
                return None
            
            doc, expiry_time = self.cache[key]
            
            # Check expiration
            if self._is_expired(expiry_time):
                # Remove expired item
                del self.cache[key]
                self.stats["expirations"] += 1
                self.stats["misses"] += 1
                return None
            
            # Move to end of OrderedDict to mark as most recently used
            self.cache.move_to_end(key)
            self.stats["hits"] += 1
            
            return doc
    
    def put(self, key: str, doc: DoclingDocument, ttl: Optional[int] = None) -> None:
        """
        Add a document to the cache.
        
        Args:
            key: Cache key for the document
            doc: The document to cache
            ttl: Optional time-to-live in seconds (overrides default_ttl)
        """
        with self.lock:
            # Calculate expiration time if TTL is provided
            expiry_time = None
            if ttl is not None:
                expiry_time = time.time() + ttl
            elif self.default_ttl is not None:
                expiry_time = time.time() + self.default_ttl
            
            # Check if we need to evict an item
            if key not in self.cache and len(self.cache) >= self.max_size:
                self._evict_if_needed()
            
            # Add or update the item
            self.cache[key] = (doc, expiry_time)
            
            # Move to end to mark as most recently used
            self.cache.move_to_end(key)
            
            self.stats["puts"] += 1
    
    def remove(self, key: str) -> bool:
        """
        Remove a document from the cache.
        
        Args:
            key: Cache key for the document
            
        Returns:
            True if the document was removed, False if it wasn't in the cache
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all documents from the cache."""
        with self.lock:
            self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary of cache statistics
        """
        with self.lock:
            stats = self.stats.copy()
            stats["size"] = len(self.cache)
            stats["max_size"] = self.max_size
            
            # Calculate hit ratio
            total_requests = stats["hits"] + stats["misses"]
            stats["hit_ratio"] = stats["hits"] / total_requests if total_requests > 0 else 0
            
            return stats


# Function decorator for document caching
def cache_document(cache: DocumentCache, key_fn: Callable = lambda *args, **kwargs: str(args[0])):
    """
    Decorator for caching document loading functions.
    
    Args:
        cache: The DocumentCache instance to use
        key_fn: Function to generate cache keys from function arguments
        
    Returns:
        Decorated function
        
    Example:
        @cache_document(my_cache)
        def load_document(doc_id: str) -> DoclingDocument:
            # Load the document from storage
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate the cache key
            cache_key = key_fn(*args, **kwargs)
            
            # Try to get from cache
            cached_doc = cache.get(cache_key)
            if cached_doc is not None:
                return cached_doc
            
            # Call the original function
            doc = func(*args, **kwargs)
            
            # Cache the result
            if doc is not None:
                cache.put(cache_key, doc)
            
            return doc
        return wrapper
    return decorator 