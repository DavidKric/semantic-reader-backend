"""
Abstract interface for document storage implementations.

This module defines the base interface that all document storage
implementations must follow to ensure consistent behavior across
different storage backends.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
import logging
from pathlib import Path

# Import the DoclingDocument from docling_core
try:
    from docling_core.types import DoclingDocument
except ImportError:
    logging.warning("docling_core not found. DoclingDocument storage will not be available.")
    # Define a stub class for type hints only
    class DoclingDocument:
        pass

logger = logging.getLogger(__name__)


class DocumentStorage(ABC):
    """
    Abstract base class for DoclingDocument storage implementations.
    
    This class defines the interface that all document storage implementations
    must follow, providing standard methods for storing, retrieving, and
    managing DoclingDocument objects.
    """
    
    @abstractmethod
    def save(self, doc: DoclingDocument, doc_id: Optional[str] = None) -> str:
        """
        Save a DoclingDocument to storage.
        
        Args:
            doc: The DoclingDocument to save
            doc_id: Optional ID for the document. If not provided, 
                    an ID will be generated.
                    
        Returns:
            The document ID used for storage
        """
        pass
    
    @abstractmethod
    def load(self, doc_id: str) -> DoclingDocument:
        """
        Load a DoclingDocument from storage.
        
        Args:
            doc_id: The ID of the document to load
            
        Returns:
            The loaded DoclingDocument
            
        Raises:
            FileNotFoundError: If the document is not found
        """
        pass
    
    @abstractmethod
    def delete(self, doc_id: str) -> bool:
        """
        Delete a DoclingDocument from storage.
        
        Args:
            doc_id: The ID of the document to delete
            
        Returns:
            True if the document was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    def list_documents(self, filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        List documents in storage, optionally filtered by criteria.
        
        Args:
            filter_criteria: Optional filter criteria to apply
            
        Returns:
            List of document metadata dictionaries
        """
        pass
    
    @abstractmethod
    def document_exists(self, doc_id: str) -> bool:
        """
        Check if a document exists in storage.
        
        Args:
            doc_id: The ID of the document to check
            
        Returns:
            True if the document exists, False otherwise
        """
        pass
    
    @abstractmethod
    def save_batch(self, docs: List[DoclingDocument], doc_ids: Optional[List[str]] = None) -> List[str]:
        """
        Save multiple DoclingDocuments to storage.
        
        Args:
            docs: List of DoclingDocument objects to save
            doc_ids: Optional list of document IDs. If not provided,
                    IDs will be generated.
                    
        Returns:
            List of document IDs used for storage
        """
        pass
    
    @abstractmethod
    def load_batch(self, doc_ids: List[str]) -> List[DoclingDocument]:
        """
        Load multiple DoclingDocuments from storage.
        
        Args:
            doc_ids: List of document IDs to load
            
        Returns:
            List of loaded DoclingDocument objects
        """
        pass 