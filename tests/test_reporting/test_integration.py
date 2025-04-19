"""
Integration tests for the reporting module.

This module tests the integration of all components in the reporting system,
including HTML generation, visualization, and API routes.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from app.dependencies.services import get_document_service
from app.main import create_app
from app.reporting.html_generator import HTMLReportGenerator
from app.reporting.service import ReportService, get_report_service
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(create_app())


@pytest.fixture
def sample_document():
    """Sample document for testing."""
    return {
        "id": "test-integration-123",
        "filename": "integration_test.pdf",
        "metadata": {
            "title": "Integration Test Document",
            "author": "Test Author",
            "creation_date": "2023-01-01",
            "page_count": 1,
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
                        "text": "This is an integration test document."
                    }
                ],
                "tables": [
                    {
                        "x0": 100,
                        "y0": 300,
                        "x1": 500,
                        "y1": 400,
                        "rows": 2,
                        "cols": 2,
                        "cells": [
                            {"row": 0, "col": 0, "x0": 100, "y0": 300, "x1": 300, "y1": 350, "text": "Cell 1"},
                            {"row": 0, "col": 1, "x0": 300, "y0": 300, "x1": 500, "y1": 350, "text": "Cell 2"},
                            {"row": 1, "col": 0, "x0": 100, "y0": 350, "x1": 300, "y1": 400, "text": "Cell 3"},
                            {"row": 1, "col": 1, "x0": 300, "y0": 350, "x1": 500, "y1": 400, "text": "Cell 4"}
                        ]
                    }
                ],
                "figures": [
                    {
                        "x0": 100,
                        "y0": 450,
                        "x1": 300,
                        "y1": 550,
                        "type": "image",
                        "caption": "Sample figure for integration testing"
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


def test_end_to_end_report_generation(temp_output_dir, sample_document):
    """Test the entire report generation process from document to HTML."""
    # Set up the service
    service = ReportService(output_dir=temp_output_dir)
    
    # Generate report
    report = service.generate_report([sample_document])
    
    # Check that the report is generated
    assert isinstance(report, str)
    assert "<title>Integration Test Document - Document Analysis Report</title>" in report
    assert "<h1>Integration Test Document</h1>" in report
    
    # Check that the report contains all required sections
    assert "<section class='metadata-section'>" in report
    assert "<section class='overview-section'>" in report
    assert "<section class='pages-section'>" in report
    
    # Check that the report contains visualizations
    assert "<div class='layout-visualization'" in report
    assert "<div class='text-visualization'" in report
    assert "<div class='tables-visualization'" in report
    assert "<div class='figures-visualization'" in report
    
    # Check that the report file was created
    report_path = Path(temp_output_dir) / f"report_{sample_document['id']}.html"
    assert report_path.exists()
    assert report_path.stat().st_size > 0


def test_api_integration(client, sample_document, temp_output_dir):
    """Test the integration of API routes with the reporting service."""
    # Override the document service dependency
    def mock_get_document_service():
        class MockDocService:
            def get_document(self, doc_id):
                return sample_document
        return MockDocService()
    client.app.dependency_overrides[get_document_service] = mock_get_document_service

    # Override the report service dependency to use the temp_output_dir
    def mock_get_report_service():
        return ReportService(output_dir=temp_output_dir)
    client.app.dependency_overrides[get_report_service] = mock_get_report_service

    # Debug: print all registered routes
    print("DEBUG: Registered routes:")
    for route in client.app.routes:
        print(route.path)

    # Generate the report via the API
    response = client.post(
        "/api/reports/generate",
        params={"document_ids": [sample_document["id"]]},
    )
    assert response.status_code == 200
    report_id = response.json()["report_id"]

    # Test the GET document report endpoint
    response = client.get(f"/api/reports/{report_id}")
    
    # Check response
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    
    # Check that the report contains expected content
    html_content = response.text
    assert "<title>Integration Test Document - Document Analysis Report</title>" in html_content
    assert "<h1>Integration Test Document</h1>" in html_content
    
    # Check that it contains all the expected sections
    assert "<section class='metadata-section'>" in html_content
    assert "<section class='overview-section'>" in html_content
    assert "<section class='pages-section'>" in html_content

    client.app.dependency_overrides = {}  # Clean up after test


@patch("app.reporting.routes")
def test_service_html_generation_integration(mock_doc_service, sample_document, temp_output_dir):
    """Test integration between service layer and HTML generator."""
    # Set up the service
    service = ReportService(output_dir=temp_output_dir)
    
    # Test that the service correctly delegates to the HTML generator
    with patch.object(service.html_generator, 'generate_report') as mock_generate:
        mock_generate.return_value = "<html>Test</html>"
        
        # Call the service
        result = service.generate_report(
            sample_document,
            include_images=False,
            include_interactive=False,
            title="Custom Title"
        )
        
        # Check that the generator was called with correct arguments
        mock_generate.assert_called_once_with(
            sample_document,
            include_images=False,
            include_interactive=False,
            title="Custom Title"
        )
        
        # Check that the result is correct
        assert result == "<html>Test</html>"


def test_visualization_integration(sample_document):
    """Test the integration of visualization functions with HTML generator."""
    # Create an HTML generator with no output
    generator = HTMLReportGenerator()
    
    # Generate a report
    report = generator.generate_report(sample_document)
    
    # Extract the visualization divs
    assert "<div class='layout-visualization'" in report
    assert "<div class='text-visualization'" in report
    assert "<div class='tables-visualization'" in report
    assert "<div class='figures-visualization'" in report 