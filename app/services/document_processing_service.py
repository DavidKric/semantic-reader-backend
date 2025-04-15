"""
Document processing service for the Semantic Reader backend.

This service coordinates document parsing, analysis, and processing operations
using both local database models and the papermage_docling library components.
"""

import logging
import tempfile
from typing import Dict, List, Any, Optional, Union, BinaryIO, Tuple
from pathlib import Path
import os
import io
import uuid
from datetime import datetime

from fastapi import UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.config import settings
from app.models.document import Document, Page, Section, Paragraph
from app.dependencies.database import get_db

# Import papermage_docling components
try:
    from papermage_docling.api_service import get_api_service
    from papermage_docling.parsers.pdf_parser import DoclingPdfParser
    DOCLING_AVAILABLE = True
except ImportError:
    logging.warning("papermage_docling not available. Document processing will be disabled.")
    DOCLING_AVAILABLE = False

from app.services.base import BaseService

logger = logging.getLogger(__name__)


class DocumentProcessingService(BaseService[Document, int]):
    """
    Service for document processing operations.
    
    This service provides methods for parsing and analyzing documents,
    extracting text, and managing the document processing pipeline.
    It integrates with both the external papermage_docling API service
    and the local database for document persistence.
    """
    
    def __init__(self, db: Session, api_service: Optional[Any] = None):
        """
        Initialize the document processing service.
        
        Args:
            db: SQLAlchemy database session
            api_service: Optional API service (if None, will be created)
        """
        super().__init__(Document, db)
        
        self.external_api_available = DOCLING_AVAILABLE
        
        if not self.external_api_available:
            logger.warning("Document processing service initialized without docling support.")
            return
            
        try:
            # Get the API service
            self.api_service = api_service or get_api_service()
            
            # Create a PDF parser
            self.pdf_parser = DoclingPdfParser(
                enable_ocr=settings.OCR_ENABLED,
                ocr_language=settings.OCR_LANGUAGE,
                detect_rtl=settings.DETECT_RTL
            )
            
            logger.info("Initialized document processing service with docling support.")
        except Exception as e:
            logger.error(f"Failed to initialize document processing service: {e}")
            self.external_api_available = False
    
    async def parse_document(
        self,
        document: Union[bytes, BinaryIO, str, Path, UploadFile],
        file_type: str = "pdf",
        options: Optional[Dict[str, Any]] = None,
        return_papermage: bool = False,
        save_result: bool = True
    ) -> Document:
        """
        Parse a document using the appropriate parser and store in database.
        
        Args:
            document: The document content or path
            file_type: The type of document (pdf, docx, etc.)
            options: Additional parsing options
            return_papermage: Whether to return PaperMage format
            save_result: Whether to save the result to storage
            
        Returns:
            Document database model with parsed data
        """
        # Default options
        if options is None:
            options = {}
        
        # Get filename
        if isinstance(document, UploadFile):
            filename = document.filename
            document_content = await document.read()
        elif isinstance(document, (str, Path)):
            filename = str(Path(document).name)
            document_content = document
        else:
            # For bytes or file-like objects, use a generic name
            filename = f"document_{uuid.uuid4()}.{file_type}"
            document_content = document
        
        # Create database record first
        db_document = self.create(
            filename=filename,
            file_type=file_type,
            processing_status="processing",
            is_processed=False,
            storage_path=None,
            # Add other metadata
            doc_metadata={}
        )
        
        try:
            # If external API is available, use it for enhanced processing
            if self.external_api_available:
                api_result = await self._process_with_external_api(document_content, file_type, options, save_result, return_papermage)
                
                # Update database record with results from API
                if api_result:
                    db_document = self._update_document_from_api_result(db_document, api_result)
            else:
                # Fallback to basic local processing
                logger.info("External API not available, using basic local processing")
                
                # Basic document metadata extraction (would be enhanced in a real implementation)
                # Note: In a real implementation, we would add local document parsing logic here
                timestamp = datetime.now().isoformat()
                
                # Update with basic metadata
                db_document = self.update(
                    db_document.id,
                    processing_status="completed",
                    is_processed=True,
                    doc_metadata={
                        "processed_at": timestamp,
                        "processing_method": "local",
                        "file_type": file_type
                    }
                )
                
                # Create basic related entities for the document
                self._create_basic_entities(db_document)
            
            return db_document
            
        except Exception as e:
            # Update document status to failed
            self.update(
                db_document.id,
                processing_status="failed",
                doc_metadata={"error": str(e)}
            )
            logger.error(f"Error processing document: {e}")
            raise
    
    async def _process_with_external_api(
        self, 
        document_content: Any, 
        file_type: str, 
        options: Dict[str, Any],
        save_result: bool,
        return_papermage: bool
    ) -> Optional[Dict[str, Any]]:
        """Process document with external API service."""
        if isinstance(document_content, (str, Path)):
            # Document is a file path
            return self.api_service.process_document(
                document_content,
                save_result=save_result,
                return_id=False,
                return_papermage=return_papermage,
                **options
            )
        else:
            # Document is bytes or file-like, create a temporary file
            with tempfile.NamedTemporaryFile(suffix=f".{file_type}", delete=False) as temp_file:
                if isinstance(document_content, bytes):
                    temp_file.write(document_content)
                else:
                    # File-like object
                    temp_file.write(document_content.read() if hasattr(document_content, 'read') else document_content)
                
                temp_file.flush()
                
                try:
                    return self.api_service.process_document(
                        temp_file.name,
                        save_result=save_result,
                        return_id=False,
                        return_papermage=return_papermage,
                        **options
                    )
                finally:
                    # Clean up temporary file
                    os.unlink(temp_file.name)
    
    def _update_document_from_api_result(self, document: Document, api_result: Dict[str, Any]) -> Document:
        """Update document model with data from API result."""
        # Extract metadata from API result
        metadata = api_result.get("metadata", {})
        language = metadata.get("language", "")
        has_rtl = metadata.get("is_rtl_language", False)
        
        # Update document model
        document = self.update(
            document.id,
            processing_status="completed",
            is_processed=True,
            storage_id=api_result.get("id"),
            language=language,
            has_rtl=has_rtl,
            doc_metadata=metadata,
            # Stats
            num_pages=len(api_result.get("pages", [])),
            word_count=len(api_result.get("words", [])),
            ocr_applied=api_result.get("ocr_applied", False)
        )
        
        # Create related entities
        self._create_related_entities(document, api_result)
        
        return document
    
    def _create_related_entities(self, document: Document, api_result: Dict[str, Any]) -> None:
        """
        Create related database entities from API result.
        
        Args:
            document: The parent document model
            api_result: The API result data
        """
        # Create pages
        for i, page_data in enumerate(api_result.get("pages", [])):
            page = Page(
                document_id=document.id,
                page_number=i + 1,
                width=page_data.get("width", 0),
                height=page_data.get("height", 0)
            )
            self.db.add(page)
        
        # Create sections if available
        for i, section_data in enumerate(api_result.get("sections", [])):
            section = Section(
                document_id=document.id,
                title=section_data.get("title", f"Section {i+1}"),
                section_type=section_data.get("type", "unknown")
            )
            self.db.add(section)
            
        # Create paragraphs if available
        for i, paragraph_data in enumerate(api_result.get("paragraphs", [])):
            paragraph = Paragraph(
                document_id=document.id,
                text=paragraph_data.get("text", ""),
                page_number=paragraph_data.get("page_number", 0)
            )
            self.db.add(paragraph)
        
        self.db.commit()
    
    def _create_basic_entities(self, document: Document) -> None:
        """
        Create basic related entities for a document (used when API is unavailable).
        
        Args:
            document: The parent document model
        """
        # Create a single page for the document as a placeholder
        page = Page(
            document_id=document.id,
            page_number=1,
            width=612,  # Standard letter width in points
            height=792  # Standard letter height in points
        )
        self.db.add(page)
        
        # Create a basic section
        section = Section(
            document_id=document.id,
            title="Main Content",
            section_type="content"
        )
        self.db.add(section)
        
        # Create a basic paragraph
        paragraph = Paragraph(
            document_id=document.id,
            text="Document content not available (processed locally)",
            page_number=1
        )
        self.db.add(paragraph)
        
        self.db.commit()
    
    async def get_document(
        self, 
        document_id: Union[str, int], 
        as_papermage: bool = False,
        sync_with_external: bool = True
    ) -> Optional[Union[Document, Dict[str, Any]]]:
        """
        Get a document by ID, with optional enrichment from external API.
        
        Args:
            document_id: The document ID (database ID or storage ID)
            as_papermage: Whether to return PaperMage format
            sync_with_external: Whether to sync with external API if available
            
        Returns:
            The document model or data
        """
        # Try to get from database first
        db_document = None
        
        if isinstance(document_id, int) or (isinstance(document_id, str) and document_id.isdigit()):
            # Numeric ID - try local DB first
            db_document = self.get_by_id(int(document_id))
        else:
            # Try to find by storage ID
            db_document = self.db.query(Document).filter(Document.storage_id == document_id).first()
        
        # If document found in database and PaperMage format not requested or API not available
        if db_document and (not as_papermage or not self.external_api_available):
            return db_document
            
        # If document found in database, has storage ID, PaperMage format requested, and external API available
        if db_document and db_document.storage_id and as_papermage and self.external_api_available:
            try:
                return self.api_service.get_document(db_document.storage_id, as_papermage=True)
            except Exception as e:
                logger.error(f"Error getting document from API: {e}")
                return db_document
        
        # If document not found in database but external API is available
        if not db_document and self.external_api_available and sync_with_external:
            try:
                # Try to get from external API
                api_result = self.api_service.get_document(document_id, as_papermage=as_papermage)
                
                if not as_papermage:
                    # Create a new database record for this external document
                    db_document = self.create(
                        filename=api_result.get("filename", f"document_{document_id}"),
                        file_type=api_result.get("file_type", "pdf"),
                        processing_status="completed",
                        is_processed=True,
                        storage_id=document_id,
                        doc_metadata=api_result.get("metadata", {})
                    )
                    
                    # Create related entities
                    self._create_related_entities(db_document, api_result)
                    
                    return db_document
                
                return api_result
                
            except Exception as e:
                logger.error(f"Error getting document from API: {e}")
                return None
        
        # Document not found in database or API
        return None
    
    async def delete_document(self, document_id: Union[str, int]) -> bool:
        """
        Delete a document by ID from both database and external storage.
        
        Args:
            document_id: The document ID (database ID or storage ID)
            
        Returns:
            True if deletion was successful
        """
        # Try to get from database first
        db_document = None
        if isinstance(document_id, int) or (isinstance(document_id, str) and document_id.isdigit()):
            # Numeric ID - try local DB
            db_document = self.get_by_id(int(document_id))
        else:
            # Try to find by storage ID
            db_document = self.db.query(Document).filter(Document.storage_id == document_id).first()
        
        # Delete from external storage if available
        api_success = False
        if db_document and db_document.storage_id and self.external_api_available:
            try:
                api_success = self.api_service.delete_document(db_document.storage_id)
            except Exception as e:
                logger.error(f"Error deleting document from API: {e}")
                # Continue with database deletion even if API fails
        
        # Delete from database if found
        db_success = False
        if db_document:
            # Delete related entities first
            self._delete_related_entities(db_document.id)
            
            # Then delete the document
            db_success = self.delete(db_document.id)
        
        return api_success or db_success
    
    def _delete_related_entities(self, document_id: int) -> None:
        """Delete all related entities for a document."""
        # Delete pages
        self.db.query(Page).filter(Page.document_id == document_id).delete()
        
        # Delete sections
        self.db.query(Section).filter(Section.document_id == document_id).delete()
        
        # Delete paragraphs
        self.db.query(Paragraph).filter(Paragraph.document_id == document_id).delete()
        
        self.db.commit()
    
    async def list_documents(
        self, 
        filter_criteria: Optional[Dict[str, Any]] = None, 
        include_external: bool = True,
        sync_with_external: bool = True,
        page: int = 1,
        page_size: int = 20
    ) -> List[Union[Document, Dict[str, Any]]]:
        """
        List available documents from database and optionally external storage.
        
        Args:
            filter_criteria: Optional filter criteria
            include_external: Whether to include documents from external storage
            sync_with_external: Whether to sync external documents with local database
            page: Page number for pagination
            page_size: Number of items per page
            
        Returns:
            List of document models or metadata
        """
        # Get documents from database
        query = self.db.query(Document)
        
        # Apply filters
        if filter_criteria:
            for key, value in filter_criteria.items():
                if hasattr(Document, key):
                    query = query.filter(getattr(Document, key) == value)
        
        # Apply sorting (newest first)
        query = query.order_by(desc(Document.created_at))
        
        # Apply pagination
        offset = (page - 1) * page_size
        db_documents = query.offset(offset).limit(page_size).all()
        
        # Get documents from external storage if requested and API available
        if include_external and self.external_api_available:
            try:
                # Get documents from external API
                api_documents = self.api_service.list_documents(filter_criteria)
                
                if sync_with_external:
                    # Find documents that are in API but not in DB
                    db_storage_ids = {doc.storage_id for doc in db_documents if doc.storage_id}
                    
                    # For each API document not in DB, create a new DB record
                    for api_doc in api_documents:
                        doc_id = api_doc.get("id")
                        if doc_id and doc_id not in db_storage_ids:
                            # Create minimal DB record
                            db_doc = self.create(
                                filename=api_doc.get("filename", f"document_{doc_id}"),
                                file_type=api_doc.get("file_type", "pdf"),
                                processing_status="completed",
                                is_processed=True,
                                storage_id=doc_id,
                                doc_metadata=api_doc.get("metadata", {})
                            )
                            db_documents.append(db_doc)
            except Exception as e:
                logger.error(f"Error listing documents from API: {e}")
                # Continue with database results only
        
        return db_documents
    
    def update_document_metadata(
        self, 
        document_id: int, 
        metadata: Dict[str, Any], 
        sync_with_external: bool = True
    ) -> Optional[Document]:
        """
        Update document metadata in the database and optionally in external storage.
        
        Args:
            document_id: The document ID
            metadata: The metadata to update
            sync_with_external: Whether to sync with external API
            
        Returns:
            Updated document or None if not found
        """
        # Get document from database
        document = self.get_by_id(document_id)
        if not document:
            return None
        
        # Update document metadata in database
        current_metadata = document.doc_metadata or {}
        updated_metadata = {**current_metadata, **metadata}
        
        document = self.update(
            document_id,
            doc_metadata=updated_metadata
        )
        
        # Sync with external API if requested and available
        if sync_with_external and self.external_api_available and document.storage_id:
            try:
                # Update metadata in external API
                self.api_service.update_document_metadata(document.storage_id, metadata)
            except Exception as e:
                logger.error(f"Error updating document metadata in API: {e}")
                # Continue even if API update fails
        
        return document
    
    def get_document_count(self, filter_criteria: Optional[Dict[str, Any]] = None) -> int:
        """
        Get the count of documents in the database.
        
        Args:
            filter_criteria: Optional filter criteria
            
        Returns:
            Number of documents
        """
        query = self.db.query(Document)
        
        # Apply filters
        if filter_criteria:
            for key, value in filter_criteria.items():
                if hasattr(Document, key):
                    query = query.filter(getattr(Document, key) == value)
        
        return query.count()
    
    def clear_document_cache(self) -> bool:
        """
        Clear the document cache.
        
        Returns:
            True if cache was cleared
        """
        if not self.external_api_available:
            logger.warning("Document processing is not available (docling not installed)")
            return False
        
        try:
            self.api_service.clear_cache()
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Get pipeline statistics.
        
        Returns:
            Dictionary of pipeline statistics
        """
        if not self.external_api_available:
            return {
                "status": "unavailable", 
                "error": "Document processing is not available (docling not installed)"
            }
        
        try:
            return self.api_service.get_pipeline_stats()
        except Exception as e:
            logger.error(f"Error getting pipeline stats: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary of cache statistics
        """
        if not self.external_api_available:
            return {
                "status": "unavailable", 
                "error": "Document processing is not available (docling not installed)"
            }
        
        try:
            return self.api_service.get_cache_stats()
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"status": "error", "message": str(e)} 