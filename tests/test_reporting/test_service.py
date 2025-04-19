"""
Tests for the report generation service.

This module tests the ReportService class that manages HTML report generation.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from app.reporting.service import ReportService, init_reporting


@pytest.fixture
def sample_document():
    """Sample document for testing."""
    return {
        "id": "test123",
        "filename": "test_document.pdf",
        "metadata": {
            "title": "Test Document",
            "author": "Test Author",
            "creation_date": "2023-01-01",
            "page_count": 2
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
                ]
            }
        ]
    }


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


def test_report_service_init(temp_output_dir):
    """Test ReportService initialization."""
    # Test with output directory
    service = ReportService(output_dir=temp_output_dir)
    assert service.output_dir == Path(temp_output_dir)
    assert Path(service.output_dir).exists()
    
    # Test html_generator initialization
    assert service.html_generator is not None
    assert service.html_generator.output_dir == Path(temp_output_dir)
    
    # Test without output directory
    service = ReportService()
    assert service.output_dir is None
    assert service.html_generator.output_dir is None


def test_generate_report(sample_document, temp_output_dir):
    """Test generating a report."""
    service = ReportService(output_dir=temp_output_dir)
    
    # Generate report
    report = service.generate_report(sample_document)
    
    # Check that report is a string
    assert isinstance(report, str)
    
    # Check that the report contains expected content
    assert "<title>Test Document - Document Analysis Report</title>" in report
    assert "<h1>Test Document</h1>" in report
    
    # Check that report file was created
    report_path = Path(temp_output_dir) / f"report_{sample_document['id']}.html"
    assert report_path.exists()


def test_get_report_path(sample_document, temp_output_dir):
    """Test getting the path to a generated report."""
    service = ReportService(output_dir=temp_output_dir)
    
    # Generate report
    service.generate_report(sample_document)
    
    # Get report path
    report_path = service.get_report_path(sample_document["id"])
    
    # Check that path exists and is correct
    assert report_path is not None
    assert report_path == Path(temp_output_dir) / f"report_{sample_document['id']}.html"
    assert report_path.exists()
    
    # Test with non-existent report
    nonexistent_path = service.get_report_path("nonexistent")
    assert nonexistent_path is None
    
    # Test with no output directory
    service = ReportService()
    assert service.get_report_path(sample_document["id"]) is None


@patch("app.reporting.service.os")
@patch("app.reporting.service.reports_router")
def test_init_reporting(mock_router, mock_os):
    """Test initializing the reporting module."""
    # Create a mock FastAPI app
    app = MagicMock()
    
    # Mock settings with REPORT_OUTPUT_DIR
    with patch("app.reporting.service.settings") as mock_settings:
        mock_settings.REPORT_OUTPUT_DIR = "/test/output/dir"
        
        # Initialize reporting
        init_reporting(app)
        
        # Check that the directory was created
        mock_os.makedirs.assert_called_once_with("/test/output/dir", exist_ok=True)
        
        # Check that the router was included
        app.include_router.assert_called_once_with(mock_router)
        
        # Check that static files were mounted
        app.mount.assert_called_once()
        
    # Test without REPORT_OUTPUT_DIR
    app = MagicMock()
    with patch("app.reporting.service.settings") as mock_settings:
        mock_settings.REPORT_OUTPUT_DIR = None
        
        # Initialize reporting
        init_reporting(app)
        
        # Check that the router was included
        app.include_router.assert_called_once_with(mock_router)
        
        # Check that static files were not mounted
        app.mount.assert_not_called()


def test_custom_report_title(sample_document, temp_output_dir):
    """Test generating a report with a custom title."""
    service = ReportService(output_dir=temp_output_dir)
    
    # Generate report with custom title
    report = service.generate_report(sample_document, title="Custom Report Title")
    
    # Check that the report contains custom title
    assert "<title>Custom Report Title - Document Analysis Report</title>" in report
    assert "<h1>Custom Report Title</h1>" in report


def test_report_without_images(sample_document, temp_output_dir):
    """Test generating a report without images."""
    service = ReportService(output_dir=temp_output_dir)
    
    # Generate report without images
    report = service.generate_report(sample_document, include_images=False)
    
    # Check that the report was generated
    assert isinstance(report, str)
    assert "<title>Test Document - Document Analysis Report</title>" in report


def test_report_without_interactive_elements(sample_document, temp_output_dir):
    """Test generating a report without interactive elements."""
    service = ReportService(output_dir=temp_output_dir)
    
    # Generate report without interactive elements
    report = service.generate_report(sample_document, include_interactive=False)
    
    # Check that the report doesn't contain interactive JavaScript
    assert "<script>" not in report or "function showPage" not in report 