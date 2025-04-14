"""
File-based storage implementation for DoclingDocument objects.

This module provides a file-based storage implementation for DoclingDocument
objects, storing them as compressed JSON files on disk.
"""

import os
import json
import gzip
import uuid
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import concurrent.futures

from papermage_docling.storage.interface import DocumentStorage

# Import the DoclingDocument from docling_core
try:
    from docling_core.types import DoclingDocument
except ImportError:
    logging.warning("docling_core not found. DoclingDocument storage will not be available.")
    # Define a stub class for type hints only
    class DoclingDocument:
        pass

logger = logging.getLogger(__name__)


class FileDocumentStorage(DocumentStorage):
    """
    File-based storage implementation for DoclingDocument objects.
    
    This class implements the DocumentStorage interface using the file system,
    storing DoclingDocument objects as compressed JSON files.
    """
    
    def __init__(self, storage_dir: Union[str, Path], compress: bool = True):
        """
        Initialize the file storage with a directory path.
        
        Args:
            storage_dir: Directory to store document files
            compress: Whether to compress the stored files using gzip
        """
        self.storage_dir = Path(storage_dir)
        self.compress = compress
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Create metadata directory
        self.metadata_dir = self.storage_dir / "_metadata"
        os.makedirs(self.metadata_dir, exist_ok=True)
        
        # Update metadata index
        self._update_metadata_index()
        
        logger.info(f"Initialized FileDocumentStorage at {self.storage_dir}")
    
    def _update_metadata_index(self):
        """Update the internal metadata index from disk."""
        self.metadata_index = {}
        metadata_path = self.metadata_dir / "index.json"
        
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    self.metadata_index = json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata index: {e}")
                # Start with empty index if there's an error
                self.metadata_index = {}
    
    def _save_metadata_index(self):
        """Save the metadata index to disk."""
        metadata_path = self.metadata_dir / "index.json"
        
        try:
            with open(metadata_path, 'w') as f:
                json.dump(self.metadata_index, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata index: {e}")
    
    def _get_file_path(self, doc_id: str) -> Path:
        """Get the file path for a document ID."""
        # Use the first 2 chars of the ID as a subdirectory to avoid
        # having too many files in a single directory
        if len(doc_id) >= 2:
            subdir = doc_id[:2]
            path = self.storage_dir / subdir
            os.makedirs(path, exist_ok=True)
            return path / f"{doc_id}.json{'.gz' if self.compress else ''}"
        else:
            return self.storage_dir / f"{doc_id}.json{'.gz' if self.compress else ''}"
    
    def _extract_metadata(self, doc: DoclingDocument) -> Dict[str, Any]:
        """Extract metadata from a DoclingDocument."""
        metadata = {}
        
        # Copy metadata from the document if available
        if hasattr(doc, "metadata") and isinstance(doc.metadata, dict):
            metadata.update(doc.metadata)
        
        # Add basic stats
        metadata["num_texts"] = len(doc.texts) if hasattr(doc, "texts") else 0
        metadata["num_tables"] = len(doc.tables) if hasattr(doc, "tables") else 0
        metadata["num_figures"] = len(doc.figures) if hasattr(doc, "figures") else 0
        metadata["num_key_value_items"] = len(doc.key_value_items) if hasattr(doc, "key_value_items") else 0
        
        return metadata
    
    def save(self, doc: DoclingDocument, doc_id: Optional[str] = None) -> str:
        """
        Save a DoclingDocument to a JSON file.
        
        Args:
            doc: The DoclingDocument to save
            doc_id: Optional ID for the document. If not provided, a UUID will be generated.
            
        Returns:
            The document ID used for storage
        """
        if doc_id is None:
            doc_id = str(uuid.uuid4())
        
        file_path = self._get_file_path(doc_id)
        
        try:
            # Convert DoclingDocument to dict (assumes it has a built-in method)
            if hasattr(doc, "model_dump"):
                # For pydantic v2+
                doc_dict = doc.model_dump()
            elif hasattr(doc, "dict"):
                # For pydantic v1
                doc_dict = doc.dict()
            else:
                # Fallback - might not capture all attributes
                logger.warning(f"Using __dict__ fallback for document serialization - may not capture all attributes")
                doc_dict = doc.__dict__
            
            # Save as JSON (compressed if enabled)
            if self.compress:
                with gzip.open(file_path, 'wt', encoding='utf-8') as f:
                    json.dump(doc_dict, f)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(doc_dict, f)
            
            # Update metadata
            metadata = self._extract_metadata(doc)
            metadata["file_path"] = str(file_path)
            metadata["doc_id"] = doc_id
            metadata["compressed"] = self.compress
            self.metadata_index[doc_id] = metadata
            self._save_metadata_index()
            
            logger.info(f"Saved document {doc_id} to {file_path}")
            return doc_id
        
        except Exception as e:
            logger.error(f"Error saving document {doc_id}: {e}")
            raise
    
    def load(self, doc_id: str) -> DoclingDocument:
        """
        Load a DoclingDocument from a file.
        
        Args:
            doc_id: The ID of the document to load
            
        Returns:
            The loaded DoclingDocument
            
        Raises:
            FileNotFoundError: If the document file is not found
        """
        if not self.document_exists(doc_id):
            raise FileNotFoundError(f"Document {doc_id} not found")
        
        file_path = self._get_file_path(doc_id)
        
        try:
            # Load from JSON (compressed if needed)
            if self.compress or str(file_path).endswith('.gz'):
                with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                    doc_dict = json.load(f)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    doc_dict = json.load(f)
            
            # Create DoclingDocument from dict
            doc = DoclingDocument.parse_obj(doc_dict)
            
            logger.info(f"Loaded document {doc_id} from {file_path}")
            return doc
        
        except Exception as e:
            logger.error(f"Error loading document {doc_id}: {e}")
            raise
    
    def delete(self, doc_id: str) -> bool:
        """
        Delete a DoclingDocument file.
        
        Args:
            doc_id: The ID of the document to delete
            
        Returns:
            True if the document was deleted, False if it wasn't found
        """
        if not self.document_exists(doc_id):
            return False
        
        file_path = self._get_file_path(doc_id)
        
        try:
            # Delete the file
            os.remove(file_path)
            
            # Remove from metadata index
            if doc_id in self.metadata_index:
                del self.metadata_index[doc_id]
                self._save_metadata_index()
            
            logger.info(f"Deleted document {doc_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    def list_documents(self, filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        List documents in storage, optionally filtered by criteria.
        
        Args:
            filter_criteria: Optional filter criteria to apply to metadata
            
        Returns:
            List of document metadata dictionaries
        """
        self._update_metadata_index()  # Refresh from disk
        
        if not filter_criteria:
            # Return all documents
            return list(self.metadata_index.values())
        
        # Apply filtering
        filtered_docs = []
        for doc_id, metadata in self.metadata_index.items():
            matches = True
            for key, value in filter_criteria.items():
                if key not in metadata or metadata[key] != value:
                    matches = False
                    break
            
            if matches:
                filtered_docs.append(metadata)
        
        return filtered_docs
    
    def document_exists(self, doc_id: str) -> bool:
        """
        Check if a document exists in storage.
        
        Args:
            doc_id: The ID of the document to check
            
        Returns:
            True if the document exists, False otherwise
        """
        file_path = self._get_file_path(doc_id)
        return file_path.exists()
    
    def save_batch(self, docs: List[DoclingDocument], doc_ids: Optional[List[str]] = None) -> List[str]:
        """
        Save multiple DoclingDocuments to storage.
        
        Uses parallel processing for better performance.
        
        Args:
            docs: List of DoclingDocument objects to save
            doc_ids: Optional list of document IDs. If not provided,
                    IDs will be generated.
                    
        Returns:
            List of document IDs used for storage
        """
        # Generate IDs if not provided
        if doc_ids is None:
            doc_ids = [str(uuid.uuid4()) for _ in range(len(docs))]
        elif len(doc_ids) != len(docs):
            raise ValueError("Number of document IDs must match number of documents")
        
        saved_ids = []
        
        # Use multithreading for file I/O bound operations
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Create a future for each document save operation
            future_to_id = {
                executor.submit(self.save, doc, doc_id): doc_id
                for doc, doc_id in zip(docs, doc_ids)
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_id):
                doc_id = future_to_id[future]
                try:
                    # Get the result (will raise exception if the operation failed)
                    future.result()
                    saved_ids.append(doc_id)
                except Exception as e:
                    logger.error(f"Error saving document {doc_id} in batch: {e}")
        
        return saved_ids
    
    def load_batch(self, doc_ids: List[str]) -> List[DoclingDocument]:
        """
        Load multiple DoclingDocuments from storage.
        
        Uses parallel processing for better performance.
        
        Args:
            doc_ids: List of document IDs to load
            
        Returns:
            List of loaded DoclingDocument objects
        """
        loaded_docs = []
        
        # Use multithreading for file I/O bound operations
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Create a future for each document load operation
            future_to_id = {
                executor.submit(self.load, doc_id): doc_id
                for doc_id in doc_ids
            }
            
            # Process results as they complete
            results = {}
            for future in concurrent.futures.as_completed(future_to_id):
                doc_id = future_to_id[future]
                try:
                    # Get the result (will raise exception if the operation failed)
                    doc = future.result()
                    results[doc_id] = doc
                except Exception as e:
                    logger.error(f"Error loading document {doc_id} in batch: {e}")
            
            # Preserve original order
            for doc_id in doc_ids:
                if doc_id in results:
                    loaded_docs.append(results[doc_id])
        
        return loaded_docs 