"""
Tests for FastAPI endpoints.

These tests verify that the API endpoints correctly handle document uploads,
error responses, and integration with the document processing pipeline.
"""

import os
import json
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

# Import application modules
try:
    from app.main import app
except ImportError:
    pytest.skip("FastAPI app not available", allow_module_level=True)

# Import test utilities
from ..conftest import TEST_DATA_DIR, TEST_EXPECTED_DIR

# Create FastAPI test client
client = TestClient(app)

@pytest.mark.parametrize("sample_name", [
    "sample1_simple",
    "sample4_tables",
])
def test_process_document_endpoint(sample_name, compare_json, expected_outputs):
    """
    Test the document processing endpoint.
    
    Args:
        sample_name: Name of the sample PDF to test
        compare_json: Fixture to compare JSON outputs
        expected_outputs: Fixture providing expected outputs
    """
    # Skip if sample PDF doesn't exist
    pdf_path = TEST_DATA_DIR / f"{sample_name}.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Sample PDF {sample_name}.pdf not found")
    
    # Open the PDF file for upload
    with open(pdf_path, "rb") as pdf_file:
        # Send POST request with the PDF file
        response = client.post(
            "/api/v1/process",
            files={"file": (pdf_path.name, pdf_file, "application/pdf")},
        )
    
    # Check response status code
    assert response.status_code == 200, f"API returned {response.status_code}: {response.text}"
    
    # Check response content type
    assert response.headers["content-type"] == "application/json"
    
    # Parse response JSON
    try:
        result = response.json()
    except json.JSONDecodeError:
        pytest.fail("Response is not valid JSON")
    
    # Check response structure
    assert "status" in result, "Response should have 'status' field"
    assert result["status"] == "success", f"Status should be 'success', got '{result.get('status')}'"
    assert "result" in result, "Response should have 'result' field"
    
    # If we have an expected output, compare with it
    expected_output = expected_outputs.get(sample_name)
    if expected_output is not None:
        assert compare_json(result["result"], expected_output), \
            f"API response doesn't match expected output for {sample_name}"

def test_invalid_file_type():
    """Test that the API correctly handles invalid file types."""
    # Create a text file
    text_file_path = TEST_DATA_DIR / "invalid.txt"
    with open(text_file_path, "w") as f:
        f.write("This is not a PDF file")
    
    # Send POST request with the text file
    with open(text_file_path, "rb") as text_file:
        response = client.post(
            "/api/v1/process",
            files={"file": ("invalid.txt", text_file, "text/plain")},
        )
    
    # Check response status code (should be 400 Bad Request)
    assert response.status_code == 400, \
        f"API should return 400 for invalid file type, got {response.status_code}"
    
    # Parse response JSON
    try:
        result = response.json()
    except json.JSONDecodeError:
        pytest.fail("Response is not valid JSON")
    
    # Check error message
    assert "detail" in result, "Error response should have 'detail' field"
    assert "PDF" in result["detail"], "Error should mention PDF file requirement"

def test_missing_file():
    """Test that the API correctly handles missing file in request."""
    # Send POST request without a file
    response = client.post("/api/v1/process")
    
    # Check response status code (should be 422 Unprocessable Entity)
    assert response.status_code == 422, \
        f"API should return 422 for missing file, got {response.status_code}"

def test_corrupted_pdf():
    """Test that the API correctly handles corrupted PDF files."""
    # Create a corrupted PDF file
    corrupt_pdf_path = TEST_DATA_DIR / "corrupt.pdf"
    with open(corrupt_pdf_path, "wb") as f:
        f.write(b"%PDF-1.7\nThis is a corrupted PDF file")
    
    # Send POST request with the corrupted PDF
    with open(corrupt_pdf_path, "rb") as pdf_file:
        response = client.post(
            "/api/v1/process",
            files={"file": ("corrupt.pdf", pdf_file, "application/pdf")},
        )
    
    # Check response status code (should be 400 Bad Request)
    assert response.status_code == 400, \
        f"API should return 400 for corrupted PDF, got {response.status_code}"
    
    # Parse response JSON
    try:
        result = response.json()
    except json.JSONDecodeError:
        pytest.fail("Response is not valid JSON")
    
    # Check error message
    assert "detail" in result, "Error response should have 'detail' field"
    assert "corrupt" in result["detail"].lower() or "invalid" in result["detail"].lower(), \
        "Error should mention corrupt or invalid PDF"

def test_pipeline_config_endpoint():
    """Test the pipeline configuration endpoint."""
    # GET request to get pipeline configuration
    response = client.get("/api/v1/pipeline/config")
    
    # Check response status code
    assert response.status_code == 200, \
        f"API returned {response.status_code}: {response.text}"
    
    # Parse response JSON
    try:
        result = response.json()
    except json.JSONDecodeError:
        pytest.fail("Response is not valid JSON")
    
    # Check response structure
    assert "status" in result, "Response should have 'status' field"
    assert result["status"] == "success", f"Status should be 'success', got '{result.get('status')}'"
    assert "config" in result, "Response should have 'config' field"
    
    # Additional checks for configuration content could be added here
    
def test_pipeline_stats_endpoint():
    """Test the pipeline statistics endpoint."""
    # GET request to get pipeline statistics
    response = client.get("/api/v1/pipeline/stats")
    
    # Check response status code
    assert response.status_code == 200, \
        f"API returned {response.status_code}: {response.text}"
    
    # Parse response JSON
    try:
        result = response.json()
    except json.JSONDecodeError:
        pytest.fail("Response is not valid JSON")
    
    # Check response structure
    assert "status" in result, "Response should have 'status' field"
    assert result["status"] == "success", f"Status should be 'success', got '{result.get('status')}'"
    assert "stats" in result, "Response should have 'stats' field"
    
    # Additional checks for statistics content could be added here
