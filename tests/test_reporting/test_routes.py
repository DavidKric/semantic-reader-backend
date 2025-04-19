"""
Tests for the reporting API routes.

This module tests the FastAPI routes for generating and serving HTML reports.
"""

from unittest.mock import patch

import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_document():
    """Sample document for testing."""
    return {
        "id": "test123",
        "filename": "test_document.pdf",
        "metadata": {
            "title": "Test Document",
            "author": "Test Author",
            "creation_date": "2023-01-01",
            "page_count": 2,
            "language": "en"
        },
        "pages": [
            {
                "width": 612,
                "height": 792,
                "text_blocks": [
                    {
                        "x0": 100,
                        "y0": 100,
                        "x1": 400,
                        "y1": 150,
                        "text": "This is a test document."
                    }
                ],
                "tables": [],
                "figures": []
            }
        ]
    }


@patch("app.reporting.routes.document_service")
def test_get_document_report(mock_doc_service, client, mock_document):
    """Test the GET document report endpoint."""
    # Mock the document service to return our sample document
    mock_doc_service.get_document.return_value = mock_document
    
    # Test the endpoint
    response = client.get("/api/reports/test123")
    
    # Check response
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    
    # Check that the report contains expected content
    html_content = response.text
    assert "<title>Test Document - Document Analysis Report</title>" in html_content
    assert "<h1>Test Document</h1>" in html_content
    
    # Verify document service was called correctly
    mock_doc_service.get_document.assert_called_once_with("test123")


@patch("app.reporting.routes.document_service")
def test_get_document_report_not_found(mock_doc_service, client):
    """Test the GET document report endpoint when document is not found."""
    # Mock the document service to return None
    mock_doc_service.get_document.return_value = None
    
    # Test the endpoint
    response = client.get("/api/reports/nonexistent")
    
    # Check response
    assert response.status_code == 404
    assert response.json() == {"detail": "Document with ID nonexistent not found"}


@patch("app.reporting.routes.document_service")
def test_get_document_report_with_parameters(mock_doc_service, client, mock_document):
    """Test the GET document report endpoint with query parameters."""
    # Mock the document service to return our sample document
    mock_doc_service.get_document.return_value = mock_document
    
    # Test the endpoint with parameters
    response = client.get("/api/reports/test123?include_images=false&include_interactive=false")
    
    # Check response
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    
    # Check that interactive elements are not included
    html_content = response.text
    assert "<script>" not in html_content or "function showPage" not in html_content


@patch("app.reporting.routes.document_service")
@patch("app.reporting.routes.report_generator")
@patch("os.path.exists")
def test_download_document_report(mock_exists, mock_report_gen, mock_doc_service, client, mock_document):
    """Test the download document report endpoint."""
    # Setup mocks
    mock_doc_service.get_document.return_value = mock_document
    mock_report_gen.generate_report.return_value = "<html>Test report</html>"
    mock_report_gen.output_dir = "/test/output/dir"
    mock_exists.return_value = False  # Simulate report not saved to disk
    
    # Test the endpoint
    response = client.get("/api/reports/download/test123")
    
    # Check response
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert response.text == "<html>Test report</html>"


@patch("app.reporting.routes.document_service")
def test_preview_document_report(mock_doc_service, client, mock_document):
    """Test the preview document report endpoint."""
    # Mock the document service to return our sample document
    mock_doc_service.get_document.return_value = mock_document
    
    # Test the endpoint
    response = client.get("/api/reports/preview/test123")
    
    # Check response
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    
    # Check that the report contains expected content
    html_content = response.text
    assert "<title>Test Document - Document Analysis Report</title>" in html_content