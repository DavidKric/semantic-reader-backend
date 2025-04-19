"""
Tests for error handling and edge cases in the document processing pipeline.

This module includes tests for handling various error conditions and edge cases,
including corrupted PDFs, malformed documents, empty pages, and other problematic inputs.
"""

import os
import tempfile
from unittest.mock import patch

import pytest
from app.core.exceptions import (
    DocumentProcessingError,
    EmptyDocumentError,
    InvalidDocumentError,
)
from app.services.pipeline_service import PipelineService

INVALID_TEST_DIR = os.path.join("tests", "data", "invalid")
EMPTY_TEST_DIR = os.path.join("tests", "data", "empty")

# Ensure test directories exist
os.makedirs(INVALID_TEST_DIR, exist_ok=True)
os.makedirs(EMPTY_TEST_DIR, exist_ok=True)


def create_corrupt_pdf():
    """Create a corrupted PDF file for testing error handling."""
    corrupt_file = os.path.join(INVALID_TEST_DIR, "corrupt.pdf")
    with open(corrupt_file, "wb") as f:
        # Write PDF header but corrupt the rest
        f.write(b"%PDF-1.7\n")
        # Add some random bytes
        f.write(os.urandom(1024))
    return corrupt_file


def create_empty_pdf():
    """Create an empty PDF file for testing."""
    empty_file = os.path.join(EMPTY_TEST_DIR, "empty.pdf")
    with open(empty_file, "wb") as f:
        # Just write PDF header
        f.write(b"%PDF-1.7\n%EOF")
    return empty_file


def create_text_file_with_pdf_extension():
    """Create a text file with PDF extension."""
    fake_pdf = os.path.join(INVALID_TEST_DIR, "fake.pdf")
    with open(fake_pdf, "w") as f:
        f.write("This is not a real PDF file")
    return fake_pdf


def create_very_large_pdf():
    """Create a very large PDF-like file that might cause memory issues."""
    large_file = os.path.join(INVALID_TEST_DIR, "large.pdf")
    with open(large_file, "wb") as f:
        f.write(b"%PDF-1.7\n")
        # Write 5MB of random data
        f.write(os.urandom(5 * 1024 * 1024))
        f.write(b"\n%EOF")
    return large_file


@pytest.fixture(scope="module")
def pipeline_service():
    """Fixture for the pipeline service."""
    return PipelineService()


@pytest.fixture(scope="module")
def corrupt_pdf():
    """Fixture to create a corrupted PDF file."""
    file_path = create_corrupt_pdf()
    yield file_path
    # Cleanup
    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.fixture(scope="module")
def empty_pdf():
    """Fixture to create an empty PDF file."""
    file_path = create_empty_pdf()
    yield file_path
    # Cleanup
    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.fixture(scope="module")
def fake_pdf():
    """Fixture to create a text file with PDF extension."""
    file_path = create_text_file_with_pdf_extension()
    yield file_path
    # Cleanup
    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.fixture(scope="module")
def large_pdf():
    """Fixture to create a very large PDF-like file."""
    file_path = create_very_large_pdf()
    yield file_path
    # Cleanup
    if os.path.exists(file_path):
        os.remove(file_path)


def test_corrupt_pdf_handling(pipeline_service, corrupt_pdf):
    """Test handling of corrupted PDF files."""
    with pytest.raises(DocumentProcessingError):
        pipeline_service.process_document(corrupt_pdf)


def test_empty_pdf_handling(pipeline_service, empty_pdf):
    """Test handling of empty PDF files."""
    with pytest.raises(EmptyDocumentError):
        pipeline_service.process_document(empty_pdf)


def test_fake_pdf_handling(pipeline_service, fake_pdf):
    """Test handling of non-PDF files with PDF extension."""
    with pytest.raises(InvalidDocumentError):
        pipeline_service.process_document(fake_pdf)


def test_nonexistent_file_handling(pipeline_service):
    """Test handling of non-existent files."""
    nonexistent_file = "nonexistent.pdf"
    with pytest.raises(FileNotFoundError):
        pipeline_service.process_document(nonexistent_file)


def test_unsupported_file_type_handling(pipeline_service):
    """Test handling of unsupported file types."""
    # Create a temporary unsupported file
    with tempfile.NamedTemporaryFile(suffix=".xyz") as temp_file:
        temp_file.write(b"This is not a supported file type")
        temp_file.flush()
        with pytest.raises(InvalidDocumentError):
            pipeline_service.process_document(temp_file.name)


def test_large_file_handling(pipeline_service, large_pdf):
    """Test handling of very large files that might cause memory issues."""
    # This test might need to be marked as slow or skipped in CI environments
    # depending on the actual processing constraints
    try:
        pipeline_service.process_document(large_pdf)
    except (DocumentProcessingError, MemoryError):
        # Either a controlled error or memory error is acceptable
        assert True
    except Exception as e:
        pytest.fail(f"Unexpected exception: {e}")


def test_malformed_content_handling():
    """Test handling of PDF files with valid structure but malformed content."""
    # Create a PDF with valid structure but malformed content
    malformed_file = os.path.join(INVALID_TEST_DIR, "malformed.pdf")
    with open(malformed_file, "wb") as f:
        f.write(b"%PDF-1.7\n")
        # Add some valid-looking but actually invalid PDF objects
        f.write(b"1 0 obj\n<< /Type /Catalog /Pages")
        f.write(b" /InvalidStructure >>\nendobj\n")
        f.write(b"%EOF")
    
    try:
        pipeline_service = PipelineService()
        with pytest.raises(DocumentProcessingError):
            pipeline_service.process_document(malformed_file)
    finally:
        # Cleanup
        if os.path.exists(malformed_file):
            os.remove(malformed_file)


def test_timeout_handling():
    """Test handling of timeouts during document processing."""
    with tempfile.NamedTemporaryFile(suffix=".pdf") as temp_file:
        # Create a complex enough file
        temp_file.write(b"%PDF-1.7\n")
        for i in range(100):
            temp_file.write(f"{i} 0 obj\n<< /Type /Page >>\nendobj\n".encode())
        temp_file.write(b"%EOF")
        temp_file.flush()
        
        # Mock the process_pages method to simulate a timeout
        with patch('app.services.pipeline_service.PipelineService.process_pages') as mock_process:
            mock_process.side_effect = TimeoutError("Processing timed out")
            
            pipeline_service = PipelineService()
            with pytest.raises(DocumentProcessingError) as excinfo:
                pipeline_service.process_document(temp_file.name)
            
            assert "Processing timed out" in str(excinfo.value)


def test_recovery_from_partial_processing_failure():
    """Test recovery from partial processing failures."""
    # Create a test document
    with tempfile.NamedTemporaryFile(suffix=".pdf") as temp_file:
        temp_file.write(b"%PDF-1.7\n")
        # Add some content to make it look like a multi-page PDF
        for i in range(5):
            temp_file.write(f"{i} 0 obj\n<< /Type /Page >>\nendobj\n".encode())
        temp_file.write(b"%EOF")
        temp_file.flush()
        
        # Mock process_page to fail on specific pages
        original_process_page = PipelineService.process_page
        
        def mock_process_page(self, page, *args, **kwargs):
            if page == 2:  # Fail on the second page
                raise Exception("Simulated failure on page 2")
            return original_process_page(self, page, *args, **kwargs)
        
        with patch('app.services.pipeline_service.PipelineService.process_page', 
                   side_effect=mock_process_page):
            pipeline_service = PipelineService()
            
            # Should continue processing other pages despite page 2 failing
            result = pipeline_service.process_document(temp_file.name)
            
            # Check if we got results for other pages
            assert result is not None
            assert "pages" in result
            # We should have 4 pages instead of 5 (one failed)
            assert len(result["pages"]) == 4


def test_api_error_response_format():
    """Test that API error responses have the correct format."""
    # This would typically be an API test, but including here for completeness
    from app.main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Test with non-existent file
    with tempfile.NamedTemporaryFile(suffix=".pdf") as temp_file:
        temp_file_name = temp_file.name
    
    # File no longer exists
    files = {"file": ("test.pdf", open(__file__, "rb"), "application/pdf")}
    response = client.post("/documents/process", files=files)
    
    # Should return a properly formatted error
    assert response.status_code == 400
    assert "error" in response.json()
    assert "message" in response.json()["error"]


def test_incomplete_pdf_handling():
    """Test handling of incomplete PDF files (truncated files)."""
    # Create a truncated PDF file
    truncated_file = os.path.join(INVALID_TEST_DIR, "truncated.pdf")
    try:
        with open(truncated_file, "wb") as f:
            f.write(b"%PDF-1.7\n")
            # Add some content but truncate before EOF
            f.write(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
            # No EOF marker
        
        pipeline_service = PipelineService()
        with pytest.raises(DocumentProcessingError):
            pipeline_service.process_document(truncated_file)
    finally:
        # Cleanup
        if os.path.exists(truncated_file):
            os.remove(truncated_file)


def test_password_protected_pdf_handling():
    """Test handling of password-protected PDF files."""
    # This test would need a real password-protected PDF
    # For now, we'll mock the exception
    with patch('app.services.pipeline_service.PipelineService.open_document') as mock_open:
        mock_open.side_effect = Exception("File is encrypted")
        
        pipeline_service = PipelineService()
        with pytest.raises(InvalidDocumentError) as excinfo:
            pipeline_service.process_document("dummy.pdf")
        
        assert "encrypted" in str(excinfo.value).lower() 