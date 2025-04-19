"""
Tests for the DocumentProcessingService.

This module contains tests for the DocumentProcessingService class,
particularly testing database integration and fallback functionality.
"""

import io
from unittest.mock import patch

import pytest
from app.models.document import Document, Page, Paragraph, Section
from app.services.document_processing_service import DocumentProcessingService
from fastapi import UploadFile


@pytest.mark.asyncio
async def test_create_document(document_service):
    """Test creating a document in the database."""
    # Create document
    document = document_service.create(
        title="Test Document",
        filename="test.pdf",
        file_type="pdf",
        processing_status="completed",
        is_processed=True
    )
    
    # Verify document was created
    assert document is not None
    assert document.id is not None
    assert document.title == "Test Document"
    assert document.filename == "test.pdf"
    assert document.processing_status == "completed"
    assert document.is_processed is True
    assert document.created_at is not None
    assert document.updated_at is not None


@pytest.mark.asyncio
async def test_get_document_by_id(document_service, sample_document):
    """Test getting a document by ID."""
    # Get document
    document = document_service.get_by_id(sample_document.id)
    
    # Verify document
    assert document is not None
    assert document.id == sample_document.id
    assert document.title == sample_document.title
    assert document.filename == sample_document.filename


@pytest.mark.asyncio
@patch('app.services.document_processing_service.DOCLING_AVAILABLE', True)
@patch.object(DocumentProcessingService, 'api_service')
async def test_list_documents_with_external(mock_api_service, document_service, sample_document, test_db):
    """Test listing documents with external API integration."""
    # Create another document
    document_service.create(
        title="Another Document",
        filename="another.pdf",
        file_type="pdf",
        processing_status="completed",
        is_processed=True
    )
    
    # Mock API service response
    mock_api_service.list_documents.return_value = [
        {
            "id": "ext-doc-id-1",
            "filename": "external_doc.pdf",
            "file_type": "pdf",
            "metadata": {
                "language": "en"
            }
        }
    ]
    
    # Set external_api_available
    document_service.external_api_available = True
    
    # List documents including external
    documents = await document_service.list_documents(include_external=True, sync_with_external=True)
    
    # Verify documents
    assert documents is not None
    assert len(documents) == 3  # 2 local + 1 external
    assert any(d.id == sample_document.id for d in documents)
    assert any(d.title == "Another Document" for d in documents)
    assert any(d.storage_id == "ext-doc-id-1" for d in documents)
    
    # Verify external document was synced to DB
    synced_doc = test_db.query(Document).filter(Document.storage_id == "ext-doc-id-1").first()
    assert synced_doc is not None
    assert synced_doc.filename == "external_doc.pdf"


@pytest.mark.asyncio
@patch('app.services.document_processing_service.DOCLING_AVAILABLE', False)
async def test_list_documents_without_external(document_service, sample_document, test_db):
    """Test listing documents without external API integration."""
    # Create another document
    document_service.create(
        title="Another Document",
        filename="another.pdf",
        file_type="pdf",
        processing_status="completed",
        is_processed=True
    )
    
    # Set external_api_available
    document_service.external_api_available = False
    
    # List documents excluding external
    documents = await document_service.list_documents(include_external=True)
    
    # Verify documents - should only have local docs since external API is disabled
    assert documents is not None
    assert len(documents) == 2
    assert any(d.id == sample_document.id for d in documents)
    assert any(d.title == "Another Document" for d in documents)


@pytest.mark.asyncio
async def test_update_document(document_service, sample_document):
    """Test updating a document."""
    # Get initial state for comparison
    initial_title = sample_document.title
    initial_status = sample_document.processing_status
    
    # Update document
    updated_document = document_service.update(
        sample_document.id,
        title="Updated Title",
        processing_status="failed"
    )
    
    # Verify document was updated
    assert updated_document is not None
    assert updated_document.id == sample_document.id
    assert updated_document.title == "Updated Title"
    assert updated_document.title != initial_title
    assert updated_document.processing_status == "failed"
    assert updated_document.processing_status != initial_status
    # Don't test timestamps as they may be the same in fast tests


@pytest.mark.asyncio
async def test_delete_document(document_service, sample_document):
    """Test deleting a document."""
    # Create related entities for the document
    page = Page(document_id=sample_document.id, page_number=1, width=100, height=100)
    section = Section(document_id=sample_document.id, title="Test Section", section_type="content", order=1)
    para = Paragraph(document_id=sample_document.id, text="Test paragraph", page_number=1, order=1)
    
    document_service.db.add_all([page, section, para])
    document_service.db.commit()
    
    # Delete document
    result = await document_service.delete_document(sample_document.id)
    
    # Verify document was deleted
    assert result is True
    
    # Verify document no longer exists
    document = document_service.get_by_id(sample_document.id)
    assert document is None
    
    # Verify related entities were deleted
    pages = document_service.db.query(Page).filter(Page.document_id == sample_document.id).all()
    sections = document_service.db.query(Section).filter(Section.document_id == sample_document.id).all()
    paragraphs = document_service.db.query(Paragraph).filter(Paragraph.document_id == sample_document.id).all()
    
    assert len(pages) == 0
    assert len(sections) == 0
    assert len(paragraphs) == 0


@pytest.mark.asyncio
@patch('app.services.document_processing_service.DOCLING_AVAILABLE', True)
@patch.object(DocumentProcessingService, '_process_with_docling')
async def test_parse_document_with_external_api(mock_process, document_service):
    """Test parsing a document with external API."""
    # Mock file content
    file_content = b"test file content"
    file = UploadFile(filename="test.pdf", file=io.BytesIO(file_content))
    
    # Set up mock return value for _process_with_docling
    # This simulates the docling library output, focusing on testing the service
    mock_process.return_value = {
        "id": "test-id",
        "metadata": {
            "language": "en",
            "is_rtl_language": False
        },
        "pages": [
            {"page_number": 1, "width": 612, "height": 792},
            {"page_number": 2, "width": 612, "height": 792}
        ],
        "words": ["word1", "word2", "word3"],
        "paragraphs": [
            {"text": "Para 1", "page_number": 1}
        ],
        "sections": [
            {"title": "Section 1", "type": "heading"}
        ]
    }
    
    # Set external_api_available
    document_service.external_api_available = True
    
    # Parse document
    document = await document_service.parse_document(
        document=file,
        file_type="pdf",
        options={"detect_rtl": True}
    )
    
    # Verify document
    assert document is not None
    assert document.id is not None
    assert document.filename == "test.pdf"
    assert document.file_type == "pdf"
    assert document.processing_status == "completed"
    assert document.is_processed is True
    assert document.storage_id == "test-id"
    assert document.language == "en"
    assert document.has_rtl is False
    assert document.num_pages == 2
    assert document.word_count == 3
    
    # Verify related entities were created
    pages = document_service.db.query(Page).filter(Page.document_id == document.id).all()
    sections = document_service.db.query(Section).filter(Section.document_id == document.id).all()
    paragraphs = document_service.db.query(Paragraph).filter(Paragraph.document_id == document.id).all()
    
    assert len(pages) == 2
    assert len(sections) == 1
    assert len(paragraphs) == 1


@pytest.mark.asyncio
@patch('app.services.document_processing_service.DOCLING_AVAILABLE', False)
async def test_parse_document_without_external_api(document_service):
    """Test parsing a document without external API."""
    # Mock file content
    file_content = b"test file content"
    file = UploadFile(filename="test.pdf", file=io.BytesIO(file_content))
    
    # Set external_api_available
    document_service.external_api_available = False
    
    # Parse document
    document = await document_service.parse_document(
        document=file,
        file_type="pdf"
    )
    
    # Verify document
    assert document is not None
    assert document.id is not None
    assert document.filename == "test.pdf"
    assert document.file_type == "pdf"
    assert document.processing_status == "completed"
    assert document.is_processed is True
    assert document.storage_id is None
    assert document.doc_metadata is not None
    assert "processing_method" in document.doc_metadata
    assert document.doc_metadata["processing_method"] == "local"
    
    # Verify basic related entities were created
    pages = document_service.db.query(Page).filter(Page.document_id == document.id).all()
    sections = document_service.db.query(Section).filter(Section.document_id == document.id).all()
    paragraphs = document_service.db.query(Paragraph).filter(Paragraph.document_id == document.id).all()
    
    assert len(pages) == 1
    assert len(sections) == 1
    assert len(paragraphs) == 1
    assert "Document content not available" in paragraphs[0].text


@pytest.mark.asyncio
@patch('app.services.document_processing_service.DOCLING_AVAILABLE', True)
@patch.object(DocumentProcessingService, 'api_service')
async def test_get_document_by_storage_id(mock_api_service, document_service):
    """Test getting a document by storage ID."""
    # Create document with storage ID
    db_document = document_service.create(
        title="Storage ID Document",
        filename="storage.pdf",
        file_type="pdf",
        processing_status="completed",
        is_processed=True,
        storage_id="storage-test-id"
    )
    
    # Set external_api_available
    document_service.external_api_available = True
    
    # Mock API service response for as_papermage=True
    mock_api_service.get_document.return_value = {
        "id": "storage-test-id",
        "papermage_format": True,
        "content": "Test content"
    }
    
    # Get document by storage ID with as_papermage=True
    result = await document_service.get_document("storage-test-id", as_papermage=True)
    
    # Verify API was called and result returned
    assert mock_api_service.get_document.called
    assert result["papermage_format"] is True
    
    # Get document by storage ID with as_papermage=False
    result = await document_service.get_document("storage-test-id", as_papermage=False)
    
    # Verify DB document was returned
    assert result.id == db_document.id
    assert result.storage_id == "storage-test-id"


@pytest.mark.asyncio
async def test_update_document_metadata(document_service, sample_document):
    """Test updating document metadata."""
    # Initial metadata
    initial_metadata = {"key1": "value1"}
    
    # Update document with initial metadata
    document_service.update(
        sample_document.id,
        doc_metadata=initial_metadata
    )
    
    # Update metadata
    updated_document = document_service.update_document_metadata(
        sample_document.id,
        {"key2": "value2", "key3": "value3"}
    )
    
    # Verify metadata was merged
    assert updated_document is not None
    assert updated_document.doc_metadata is not None
    assert updated_document.doc_metadata["key1"] == "value1"
    assert updated_document.doc_metadata["key2"] == "value2"
    assert updated_document.doc_metadata["key3"] == "value3"


@pytest.mark.asyncio
@patch('app.services.document_processing_service.DOCLING_AVAILABLE', False)
async def test_pipeline_stats_without_external_api(document_service):
    """Test getting pipeline stats without external API."""
    # Set external_api_available
    document_service.external_api_available = False
    
    # Get pipeline stats
    stats = document_service.get_pipeline_stats()
    
    # Verify stats indicates unavailability
    assert stats is not None
    assert stats["status"] == "unavailable"
    assert "error" in stats 