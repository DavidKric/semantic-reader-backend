"""
API service implementation for document processing.

This module provides a RESTful API service for document processing,
using DoclingDocument as the core data structure and handling
format conversions at API boundaries.
"""

import os
import json
import time
import logging
import tempfile
from typing import Dict, List, Any, Optional, Union, BinaryIO
from pathlib import Path

# Import the DoclingDocument from docling_core
try:
    from docling_core.types import DoclingDocument
except ImportError:
    logging.warning("docling_core not found. API service will not be available.")
    # Define a stub class for type hints only
    class DoclingDocument:
        pass

# Import adapters for format conversion
from papermage_docling.adapters import PaperMageAdapter

# Import pipeline
from papermage_docling.pipeline import SimplePipeline

# Import storage
from papermage_docling.storage import FileDocumentStorage, LRUDocumentCache

logger = logging.getLogger(__name__)


class DoclingApiService:
    """
    API service for document processing using DoclingDocument.
    
    This class provides a high-level API for document processing,
    using DoclingDocument as the core data structure and handling
    format conversions at API boundaries.
    """
    
    def __init__(
        self,
        storage_dir: Optional[Union[str, Path]] = None,
        cache_size: int = 100,
        default_ttl: Optional[int] = 3600  # 1 hour
    ):
        """
        Initialize the API service.
        
        Args:
            storage_dir: Directory to store documents (defaults to temporary directory)
            cache_size: Maximum number of documents to cache
            default_ttl: Default cache TTL in seconds (None for no expiration)
        """
        # Create storage directory if not provided
        if storage_dir is None:
            storage_dir = os.path.join(tempfile.gettempdir(), "docling_documents")
        
        # Create storage
        self.storage = FileDocumentStorage(storage_dir, compress=True)
        
        # Create cache
        self.cache = LRUDocumentCache(max_size=cache_size, default_ttl=default_ttl)
        
        # Create pipeline
        self.pipeline = SimplePipeline.create_default_pipeline()
        
        logger.info(f"Initialized DoclingApiService with storage at {storage_dir}")
    
    def process_document(
        self,
        document: Union[bytes, BinaryIO, str, Path],
        save_result: bool = True,
        return_id: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], DoclingDocument, str]:
        """
        Process a document through the pipeline.
        
        Args:
            document: Document file content, file-like object, or path
            save_result: Whether to save the result to storage
            return_id: Whether to return just the document ID (requires save_result=True)
            **kwargs: Additional processing options
            
        Returns:
            Processed document (dict, DoclingDocument, or ID depending on options)
        """
        # Handle different input types
        temp_file = None
        try:
            # Create a temporary file if needed
            if isinstance(document, bytes):
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                temp_file.write(document)
                temp_file.close()
                file_path = temp_file.name
            elif hasattr(document, 'read'):
                # File-like object
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                temp_file.write(document.read())
                temp_file.close()
                file_path = temp_file.name
            else:
                # String or Path
                file_path = str(document)
            
            # Process the document
            start_time = time.time()
            doc = self.pipeline.process_file(file_path, **kwargs)
            processing_time = time.time() - start_time
            
            logger.info(f"Processed document in {processing_time:.2f}s")
            
            # Save the result if requested
            doc_id = None
            if save_result:
                doc_id = self.storage.save(doc)
                self.cache.put(doc_id, doc)
                logger.info(f"Saved processed document with ID: {doc_id}")
            
            # Return based on options
            if return_id and save_result:
                return doc_id
            elif kwargs.get("return_papermage", False):
                # Convert to PaperMage format at API boundary
                return self.pipeline.to_papermage(doc)
            else:
                return doc
        
        finally:
            # Clean up temporary file if created
            if temp_file is not None:
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
    
    def process_papermage(
        self,
        papermage_doc: Dict[str, Any],
        save_result: bool = True,
        return_id: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], DoclingDocument, str]:
        """
        Process a PaperMage document through the pipeline.
        
        Args:
            papermage_doc: PaperMage document dict
            save_result: Whether to save the result to storage
            return_id: Whether to return just the document ID (requires save_result=True)
            **kwargs: Additional processing options
            
        Returns:
            Processed document (dict, DoclingDocument, or ID depending on options)
        """
        # Convert PaperMage to DoclingDocument at API boundary
        doc = self.pipeline.from_papermage(papermage_doc)
        
        # Process the document
        start_time = time.time()
        doc = self.pipeline.process(doc, **kwargs)
        processing_time = time.time() - start_time
        
        logger.info(f"Processed PaperMage document in {processing_time:.2f}s")
        
        # Save the result if requested
        doc_id = None
        if save_result:
            doc_id = self.storage.save(doc)
            self.cache.put(doc_id, doc)
            logger.info(f"Saved processed document with ID: {doc_id}")
        
        # Return based on options
        if return_id and save_result:
            return doc_id
        elif kwargs.get("return_papermage", False):
            # Convert back to PaperMage format at API boundary
            return self.pipeline.to_papermage(doc)
        else:
            return doc
    
    def get_document(
        self,
        doc_id: str,
        as_papermage: bool = False
    ) -> Union[DoclingDocument, Dict[str, Any]]:
        """
        Get a document from storage.
        
        Args:
            doc_id: Document ID
            as_papermage: Whether to convert to PaperMage format
            
        Returns:
            The document (DoclingDocument or dict)
        """
        # Try to get from cache
        doc = self.cache.get(doc_id)
        
        # If not in cache, load from storage
        if doc is None:
            doc = self.storage.load(doc_id)
            # Add to cache
            self.cache.put(doc_id, doc)
        
        # Convert if requested
        if as_papermage:
            return self.pipeline.to_papermage(doc)
        else:
            return doc
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from storage.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if the document was deleted, False otherwise
        """
        # Remove from cache
        self.cache.remove(doc_id)
        
        # Delete from storage
        return self.storage.delete(doc_id)
    
    def list_documents(
        self,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        List documents in storage.
        
        Args:
            filter_criteria: Optional filter criteria
            
        Returns:
            List of document metadata
        """
        return self.storage.list_documents(filter_criteria)
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Get pipeline statistics.
        
        Returns:
            Dictionary of pipeline statistics
        """
        return self.pipeline.get_stats()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary of cache statistics
        """
        return self.cache.get_stats()


# Global instance for convenience
_api_service = None

def get_api_service(**kwargs) -> DoclingApiService:
    """
    Get or create a global API service instance.
    
    Args:
        **kwargs: Configuration options for the API service
        
    Returns:
        DoclingApiService instance
    """
    global _api_service
    if _api_service is None:
        _api_service = DoclingApiService(**kwargs)
    return _api_service
