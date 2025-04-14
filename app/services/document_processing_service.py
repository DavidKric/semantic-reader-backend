"""
Document processing service for the Semantic Reader backend.

This service coordinates document parsing, analysis, and processing operations
using the papermage_docling library components.
"""

import logging
import tempfile
from typing import Dict, List, Any, Optional, Union, BinaryIO
from pathlib import Path
import os
import io

from app.core.config import settings

# Import papermage_docling components
try:
    from papermage_docling.api_service import get_api_service
    from papermage_docling.pipeline import SimplePipeline
    from papermage_docling.parsers.docling_pdf_parser import DoclingPdfParser
    from papermage_docling.converters import DoclingToPaperMageConverter
    # Import Docling document types
    try:
        from docling_core.types import DoclingDocument
    except ImportError:
        class DoclingDocument:
            pass
    DOCLING_AVAILABLE = True
except ImportError:
    logging.warning("papermage_docling not available. Document processing will be disabled.")
    DOCLING_AVAILABLE = False

from app.services.base import BaseService

logger = logging.getLogger(__name__)


class DocumentProcessingService(BaseService):
    """
    Service for document processing operations.
    
    This service provides methods for parsing and analyzing documents,
    extracting text, and managing the document processing pipeline.
    """
    
    def __init__(self):
        """Initialize the document processing service."""
        super().__init__()
        
        if not DOCLING_AVAILABLE:
            logger.warning("Document processing service initialized without docling support.")
            return
            
        try:
            # Get the API service
            self.api_service = get_api_service()
            
            # Create a PDF parser
            self.pdf_parser = DoclingPdfParser(
                enable_ocr=settings.OCR_ENABLED,
                ocr_language=settings.OCR_LANGUAGE,
                detect_rtl=settings.DETECT_RTL
            )
            
            logger.info("Initialized document processing service with docling support.")
        except Exception as e:
            logger.error(f"Failed to initialize document processing service: {e}")
            raise
    
    def parse_document(
        self,
        document: Union[bytes, BinaryIO, str, Path],
        file_type: str = "pdf",
        options: Optional[Dict[str, Any]] = None,
        return_papermage: bool = False,
        save_result: bool = True
    ) -> Dict[str, Any]:
        """
        Parse a document using the appropriate parser.
        
        Args:
            document: The document content or path
            file_type: The type of document (pdf, docx, etc.)
            options: Additional parsing options
            return_papermage: Whether to return PaperMage format
            save_result: Whether to save the result to storage
            
        Returns:
            Parsed document data
        """
        if not DOCLING_AVAILABLE:
            raise ValueError("Document processing is not available (docling not installed)")
        
        # Default options
        if options is None:
            options = {}
        
        # Use the API service for processing
        if isinstance(document, (str, Path)):
            # Document is a file path
            return self.api_service.process_document(
                document,
                save_result=save_result,
                return_id=False,
                return_papermage=return_papermage,
                **options
            )
        else:
            # Document is bytes or file-like, create a temporary file
            with tempfile.NamedTemporaryFile(suffix=f".{file_type}", delete=False) as temp_file:
                if isinstance(document, bytes):
                    temp_file.write(document)
                else:
                    # File-like object
                    temp_file.write(document.read())
                
                temp_file.flush()
                
                try:
                    result = self.api_service.process_document(
                        temp_file.name,
                        save_result=save_result,
                        return_id=False,
                        return_papermage=return_papermage,
                        **options
                    )
                    
                    return result
                finally:
                    # Clean up temporary file
                    os.unlink(temp_file.name)
    
    def get_document(self, document_id: str, as_papermage: bool = False) -> Dict[str, Any]:
        """
        Get a document by ID.
        
        Args:
            document_id: The document ID
            as_papermage: Whether to return PaperMage format
            
        Returns:
            The document data
        """
        if not DOCLING_AVAILABLE:
            raise ValueError("Document processing is not available (docling not installed)")
        
        return self.api_service.get_document(document_id, as_papermage=as_papermage)
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document by ID.
        
        Args:
            document_id: The document ID
            
        Returns:
            True if deletion was successful
        """
        if not DOCLING_AVAILABLE:
            raise ValueError("Document processing is not available (docling not installed)")
        
        return self.api_service.delete_document(document_id)
    
    def list_documents(self, filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        List available documents.
        
        Args:
            filter_criteria: Optional filter criteria
            
        Returns:
            List of document metadata
        """
        if not DOCLING_AVAILABLE:
            raise ValueError("Document processing is not available (docling not installed)")
        
        return self.api_service.list_documents(filter_criteria)
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Get pipeline statistics.
        
        Returns:
            Dictionary of pipeline statistics
        """
        if not DOCLING_AVAILABLE:
            raise ValueError("Document processing is not available (docling not installed)")
        
        return self.api_service.get_pipeline_stats()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary of cache statistics
        """
        if not DOCLING_AVAILABLE:
            raise ValueError("Document processing is not available (docling not installed)")
        
        return self.api_service.get_cache_stats() 