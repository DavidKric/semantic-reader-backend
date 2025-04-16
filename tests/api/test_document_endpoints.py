"""
Tests for document processing API endpoints.

This module contains tests for all document-related API endpoints, including
document uploading, processing, retrieval, and error handling.
"""

import os
import json
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.exceptions import (
    DocumentProcessingError,
    InvalidDocumentError,
    EmptyDocumentError
)

client = TestClient(app)


@pytest.fixture
def sample_pdf():
    """Create a simple valid PDF for testing."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        # Write a minimal valid PDF
        temp_file.write(b"%PDF-1.7\n")
        temp_file.write(b"1 0 obj\n<< /Type /Catalog >>\nendobj\n")
        temp_file.write(b"2 0 obj\n<< /Type /Pages >>\nendobj\n")
        temp_file.write(b"%EOF")
        temp_file.flush()
        file_path = temp_file.name
    
    yield file_path
    
    # Cleanup
    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.fixture
def sample_document_response():
    """Return a sample document processing response."""
    return {
        "id": "test_doc_123",
        "filename": "test.pdf",
        "pages": [
            {
                "page_number": 1,
                "width": 612,
                "height": 792,
                "text_blocks": [],
                "tables": [],
                "figures": []
            }
        ],
        "metadata": {
            "title": "Test Document",
            "author": "Test Author",
            "creation_date": "2023-01-01",
            "page_count": 1
        }
    }


def test_process_document_endpoint_success(sample_pdf, sample_document_response):
    """Test successful document processing endpoint."""
    # Mock the pipeline service to return a sample response
    with patch('app.api.routes.documents.PipelineService') as MockPipelineService:
        mock_instance = MockPipelineService.return_value
        mock_instance.process_document.return_value = sample_document_response
        
        with open(sample_pdf, "rb") as file:
            response = client.post(
                "/documents/process",
                files={"file": ("test.pdf", file, "application/pdf")}
            )
        
        assert response.status_code == 200
        assert response.json() == sample_document_response
        mock_instance.process_document.assert_called_once()


def test_process_document_endpoint_with_params(sample_pdf, sample_document_response):
    """Test document processing with query parameters."""
    # Mock the pipeline service to return a sample response
    with patch('app.api.routes.documents.PipelineService') as MockPipelineService:
        mock_instance = MockPipelineService.return_value
        mock_instance.process_document.return_value = sample_document_response
        
        with open(sample_pdf, "rb") as file:
            response = client.post(
                "/documents/process?extract_tables=true&extract_figures=true&language=en",
                files={"file": ("test.pdf", file, "application/pdf")}
            )
        
        assert response.status_code == 200
        assert response.json() == sample_document_response
        
        # Verify correct parameters were passed
        _, kwargs = mock_instance.process_document.call_args
        assert kwargs.get("extract_tables") is True
        assert kwargs.get("extract_figures") is True
        assert kwargs.get("language") == "en"


def test_process_document_endpoint_invalid_file():
    """Test document processing with invalid file."""
    # Create an invalid file (not a PDF)
    with tempfile.NamedTemporaryFile(suffix=".txt") as temp_file:
        temp_file.write(b"This is not a PDF file")
        temp_file.flush()
        
        with open(temp_file.name, "rb") as file:
            response = client.post(
                "/documents/process",
                files={"file": ("test.txt", file, "text/plain")}
            )
        
        assert response.status_code == 400
        assert "error" in response.json()
        assert "Invalid document format" in response.json()["error"]["message"]


def test_process_document_endpoint_processing_error(sample_pdf):
    """Test document processing with error during processing."""
    # Mock the pipeline service to raise an error
    with patch('app.api.routes.documents.PipelineService') as MockPipelineService:
        mock_instance = MockPipelineService.return_value
        mock_instance.process_document.side_effect = DocumentProcessingError("Processing failed")
        
        with open(sample_pdf, "rb") as file:
            response = client.post(
                "/documents/process",
                files={"file": ("test.pdf", file, "application/pdf")}
            )
        
        assert response.status_code == 500
        assert "error" in response.json()
        assert "Processing failed" in response.json()["error"]["message"]


def test_process_document_endpoint_empty_document(sample_pdf):
    """Test document processing with empty document."""
    # Mock the pipeline service to raise an EmptyDocumentError
    with patch('app.api.routes.documents.PipelineService') as MockPipelineService:
        mock_instance = MockPipelineService.return_value
        mock_instance.process_document.side_effect = EmptyDocumentError("Document is empty")
        
        with open(sample_pdf, "rb") as file:
            response = client.post(
                "/documents/process",
                files={"file": ("test.pdf", file, "application/pdf")}
            )
        
        assert response.status_code == 400
        assert "error" in response.json()
        assert "Document is empty" in response.json()["error"]["message"]


def test_get_document_endpoint(sample_document_response):
    """Test retrieving a specific document."""
    # Mock the document service to return a sample document
    with patch('app.api.routes.documents.DocumentService') as MockDocumentService:
        mock_instance = MockDocumentService.return_value
        mock_instance.get_document.return_value = sample_document_response
        
        response = client.get("/documents/test_doc_123")
        
        assert response.status_code == 200
        assert response.json() == sample_document_response
        mock_instance.get_document.assert_called_once_with("test_doc_123")


def test_get_document_endpoint_not_found():
    """Test retrieving a non-existent document."""
    # Mock the document service to return None (document not found)
    with patch('app.api.routes.documents.DocumentService') as MockDocumentService:
        mock_instance = MockDocumentService.return_value
        mock_instance.get_document.return_value = None
        
        response = client.get("/documents/nonexistent_id")
        
        assert response.status_code == 404
        assert "error" in response.json()
        assert "not found" in response.json()["error"]["message"].lower()


def test_list_documents_endpoint():
    """Test listing all documents."""
    sample_documents = [
        {"id": "doc1", "filename": "test1.pdf"},
        {"id": "doc2", "filename": "test2.pdf"}
    ]
    
    # Mock the document service to return a list of documents
    with patch('app.api.routes.documents.DocumentService') as MockDocumentService:
        mock_instance = MockDocumentService.return_value
        mock_instance.list_documents.return_value = sample_documents
        
        response = client.get("/documents")
        
        assert response.status_code == 200
        assert response.json() == sample_documents
        mock_instance.list_documents.assert_called_once()


def test_list_documents_endpoint_with_filters():
    """Test listing documents with filters."""
    sample_documents = [{"id": "doc1", "filename": "test1.pdf"}]
    
    # Mock the document service to return a filtered list
    with patch('app.api.routes.documents.DocumentService') as MockDocumentService:
        mock_instance = MockDocumentService.return_value
        mock_instance.list_documents.return_value = sample_documents
        
        response = client.get("/documents?limit=10&offset=0&sort=date_desc")
        
        assert response.status_code == 200
        assert response.json() == sample_documents
        
        # Verify correct parameters were passed
        _, kwargs = mock_instance.list_documents.call_args
        assert kwargs.get("limit") == 10
        assert kwargs.get("offset") == 0
        assert kwargs.get("sort") == "date_desc"


def test_delete_document_endpoint():
    """Test deleting a document."""
    # Mock the document service's delete_document method
    with patch('app.api.routes.documents.DocumentService') as MockDocumentService:
        mock_instance = MockDocumentService.return_value
        mock_instance.delete_document.return_value = True
        
        response = client.delete("/documents/test_doc_123")
        
        assert response.status_code == 204
        mock_instance.delete_document.assert_called_once_with("test_doc_123")


def test_delete_document_endpoint_not_found():
    """Test deleting a non-existent document."""
    # Mock the document service to return False (document not found)
    with patch('app.api.routes.documents.DocumentService') as MockDocumentService:
        mock_instance = MockDocumentService.return_value
        mock_instance.delete_document.return_value = False
        
        response = client.delete("/documents/nonexistent_id")
        
        assert response.status_code == 404
        assert "error" in response.json()
        assert "not found" in response.json()["error"]["message"].lower()


def test_update_document_metadata_endpoint(sample_document_response):
    """Test updating document metadata."""
    update_data = {
        "metadata": {
            "title": "Updated Title",
            "tags": ["test", "update"]
        }
    }
    
    # Mock the document service to return the updated document
    with patch('app.api.routes.documents.DocumentService') as MockDocumentService:
        mock_instance = MockDocumentService.return_value
        updated_doc = sample_document_response.copy()
        updated_doc["metadata"].update(update_data["metadata"])
        mock_instance.update_document_metadata.return_value = updated_doc
        
        response = client.patch(
            "/documents/test_doc_123/metadata",
            json=update_data
        )
        
        assert response.status_code == 200
        assert response.json() == updated_doc
        mock_instance.update_document_metadata.assert_called_once_with(
            "test_doc_123", update_data["metadata"]
        )


def test_update_document_metadata_endpoint_not_found():
    """Test updating metadata for a non-existent document."""
    update_data = {"metadata": {"title": "Updated Title"}}
    
    # Mock the document service to return None (document not found)
    with patch('app.api.routes.documents.DocumentService') as MockDocumentService:
        mock_instance = MockDocumentService.return_value
        mock_instance.update_document_metadata.return_value = None
        
        response = client.patch(
            "/documents/nonexistent_id/metadata",
            json=update_data
        )
        
        assert response.status_code == 404
        assert "error" in response.json()
        assert "not found" in response.json()["error"]["message"].lower()


def test_health_check_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_documentation():
    """Test that API documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Swagger UI" in response.text


def test_process_document_with_large_file():
    """Test processing a large file (slow test)."""
    # Create a larger temporary file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        # Write a minimal valid PDF with repeated content to make it larger
        temp_file.write(b"%PDF-1.7\n")
        # Add repeating content to increase file size
        for i in range(1000):
            temp_file.write(f"{i} 0 obj\n<< /Type /Page >>\nendobj\n".encode())
        temp_file.write(b"%EOF")
        temp_file.flush()
        file_path = temp_file.name
        
    try:
        # Mock the pipeline service to simulate processing time
        with patch('app.api.routes.documents.PipelineService') as MockPipelineService:
            mock_instance = MockPipelineService.return_value
            mock_response = {
                "id": "large_doc_123",
                "filename": "large_test.pdf",
                "pages": [{"page_number": i+1} for i in range(10)],
                "metadata": {"page_count": 10}
            }
            mock_instance.process_document.return_value = mock_response
            
            with open(file_path, "rb") as file:
                # Use a longer timeout for this test
                response = client.post(
                    "/documents/process",
                    files={"file": ("large_test.pdf", file, "application/pdf")}
                )
            
            assert response.status_code == 200
            assert response.json() == mock_response
    finally:
        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)


def test_concurrent_document_processing():
    """Test processing multiple documents concurrently."""
    # This is a more advanced test that would typically be implemented 
    # with a proper async testing framework
    
    # For this example, we'll mock the behavior
    with patch('app.api.routes.documents.PipelineService') as MockPipelineService:
        mock_instance = MockPipelineService.return_value
        
        # Create a simple counter to track concurrent requests
        counter = {"value": 0, "max": 0}
        
        def mock_process(file_path, **kwargs):
            counter["value"] += 1
            counter["max"] = max(counter["max"], counter["value"])
            # Simulate some processing time
            import time
            time.sleep(0.1)
            counter["value"] -= 1
            return {"id": f"doc_{file_path}", "filename": file_path}
        
        mock_instance.process_document.side_effect = mock_process
        
        # Create multiple temporary files
        files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_file.write(b"%PDF-1.7\n%EOF")
                temp_file.flush()
                files.append(temp_file.name)
        
        try:
            # Process files concurrently (in a real test, this would use asyncio)
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for file_path in files:
                    def process_file(path):
                        with open(path, "rb") as file:
                            return client.post(
                                "/documents/process",
                                files={"file": (os.path.basename(path), file, "application/pdf")}
                            )
                    
                    futures.append(executor.submit(process_file, file_path))
                
                # Get all results
                responses = [future.result() for future in futures]
            
            # Check that all responses were successful
            for response in responses:
                assert response.status_code == 200
            
            # Check that we had concurrent processing
            assert counter["max"] > 1
        
        finally:
            # Cleanup
            for file_path in files:
                if os.path.exists(file_path):
                    os.remove(file_path)


def test_rate_limiting():
    """Test rate limiting for API endpoints."""
    # This test depends on the actual rate limiting configuration
    # We'll make multiple requests in quick succession
    
    # For testing purposes, patch the rate limiter to have a very low limit
    with patch('app.api.dependencies.RateLimiter.is_rate_limited') as mock_rate_limited:
        # Make the third request hit the rate limit
        mock_rate_limited.side_effect = [False, False, True, True]
        
        # Make multiple requests to the health endpoint (lightweight)
        responses = [client.get("/health") for _ in range(4)]
        
        # First two should succeed, next two should be rate limited
        assert responses[0].status_code == 200
        assert responses[1].status_code == 200
        assert responses[2].status_code == 429  # Too Many Requests
        assert responses[3].status_code == 429
        
        # Check error message in rate limited response
        assert "error" in responses[2].json()
        assert "rate limit" in responses[2].json()["error"]["message"].lower()


def test_api_error_handling():
    """Test global error handling in the API."""
    # Mock the document service to raise an unexpected error
    with patch('app.api.routes.documents.DocumentService') as MockDocumentService:
        mock_instance = MockDocumentService.return_value
        mock_instance.get_document.side_effect = Exception("Unexpected server error")
        
        response = client.get("/documents/test_id")
        
        # Should return a 500 error with a proper error message
        assert response.status_code == 500
        assert "error" in response.json()
        assert "Internal server error" in response.json()["error"]["message"] 