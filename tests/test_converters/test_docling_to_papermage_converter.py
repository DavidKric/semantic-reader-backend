"""
Tests for the Docling to PaperMage conversion functions.

This module contains unit tests for the convert_document and docling_to_papermage functions
which convert between Docling document formats and PaperMage JSON.
"""

import json
from unittest.mock import MagicMock, patch, mock_open
import os
from pathlib import Path
from typing import Dict, Any, BinaryIO, Union

import pytest

from papermage_docling.converter import (
    convert_document,
    docling_to_papermage,
)

# Import our document structure
from papermage_docling.converters.document import Box, Document, Entity, Span

# Skip tests if Docling dependencies are not available
try:
    from docling.backend.abstract_backend import DoclingDocument
    from docling.backend.docling_parse_v4_backend import PdfDocument
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

# Get test fixtures directory from conftest.py (or define directly if needed)
TEST_DIR = Path(__file__).parent.parent
TEST_DATA_DIR = TEST_DIR / "data"
TEST_FIXTURES_DIR = TEST_DATA_DIR / "fixtures"
TEST_SAMPLES_DIR = TEST_FIXTURES_DIR / "samples"

# Create fixtures for testing
@pytest.fixture
def mock_pdf_document():
    """Create a mock PdfDocument for testing."""
    mock_doc = MagicMock(spec=PdfDocument)
    
    # Mock page
    mock_page = MagicMock()
    mock_page.width = 612
    mock_page.height = 792
    
    # Mock line
    mock_line = MagicMock()
    mock_line.text = "This is a test line."
    mock_line.bbox.x0 = 50
    mock_line.bbox.y0 = 100
    mock_line.bbox.x1 = 500
    mock_line.bbox.y1 = 120
    
    # Mock word
    mock_word = MagicMock()
    mock_word.text = "test"
    mock_word.bbox.x0 = 120
    mock_word.bbox.y0 = 100
    mock_word.bbox.x1 = 150
    mock_word.bbox.y1 = 120
    
    # Set up structure
    mock_line.words = [mock_word]
    mock_page.lines = [mock_line]
    mock_doc.pages = [mock_page]
    mock_doc.filename = "test.pdf"
    
    # Add read method to mock document to simulate file-like behavior
    mock_doc.read = MagicMock(return_value=b"%PDF-1.4\nTest PDF content")
    
    return mock_doc


@pytest.fixture
def mock_docling_document():
    """Create a mock Docling document for testing."""
    mock_doc = MagicMock()
    # Required fields for Document
    mock_doc.id = "test-123"
    mock_doc.pages = []
    mock_doc.metadata = MagicMock()
    mock_doc.metadata.language = "en"
    return mock_doc


# Test PdfDocument conversion
@pytest.mark.skipif(not DOCLING_AVAILABLE, reason="Docling dependencies not available")
@patch('papermage_docling.converter.DocumentConverter')
def test_convert_pdf_document(mock_converter):
    """Test conversion of PDF file path to PaperMage format."""
    # Mock the DocumentConverter
    converter_instance = MagicMock()
    mock_converter.return_value = converter_instance
    
    # Create a mock document
    mock_doc = MagicMock()
    mock_doc.id = "test-123"
    mock_doc.pages = []
    mock_doc.metadata = MagicMock()
    mock_doc.metadata.language = "en"
    
    # Mock the conversion result
    conversion_result = MagicMock()
    conversion_result.document = mock_doc
    converter_instance.convert.return_value = conversion_result
    
    # Use a string path as input (this is what convert_document expects)
    test_pdf_path = "test.pdf"
    
    # Convert the document
    with patch('papermage_docling.converter.docling_to_papermage') as mock_to_papermage:
        mock_to_papermage.return_value = {"id": "test-doc", "metadata": {}, "pages": [], "full_text": "Test"}
        result = convert_document(test_pdf_path)
    
    # Verify the result
    assert isinstance(result, dict)
    assert mock_to_papermage.called
    # Verify that convert was called with the string path
    converter_instance.convert.assert_called_once_with(test_pdf_path)


# Test DoclingDocument conversion
@pytest.mark.skipif(not DOCLING_AVAILABLE, reason="Docling dependencies not available")
def test_docling_to_papermage_conversion(mock_docling_document):
    """Test conversion from Docling document to PaperMage format."""
    # Convert the document
    result = docling_to_papermage(mock_docling_document)
    
    # Verify the structure of the result
    assert isinstance(result, dict)
    assert "id" in result
    assert "metadata" in result
    assert "pages" in result
    
    # Check that values from the mock document are used
    assert result["id"] == mock_docling_document.id


# Test JSON format validation
def test_validate_papermage_format():
    """Test validation of PaperMage document format."""
    # Create a valid document
    doc = Document(
        id="test-doc",  # Required field
        symbols="Test document",
        metadata={"version": "0.18.0"},
        entities={
            "pages": [
                Entity(
                    id="page-1",  # Required field
                    spans=[Span(start=0, end=12)],
                    boxes=[Box(x0=0, y0=0, x1=100, y1=100, page=0)],
                    text="Test document"
                )
            ]
        }
    )
    
    # Validate basic structure
    result = doc.model_dump()
    assert "id" in result
    assert "metadata" in result
    assert "entities" in result


# Test bytes-like input
@pytest.mark.skipif(not DOCLING_AVAILABLE, reason="Docling dependencies not available")
@patch('papermage_docling.converter.DocumentConverter')
@patch('tempfile.NamedTemporaryFile')
def test_convert_document_bytes(mock_temp_file, mock_converter):
    """Test conversion with bytes input."""
    # Mock tempfile
    mock_file = MagicMock()
    mock_file.name = "/tmp/test.pdf"
    mock_temp_file.return_value.__enter__.return_value = mock_file
    
    # Mock the DocumentConverter
    converter_instance = MagicMock()
    mock_converter.return_value = converter_instance
    
    # Create mock result
    mock_doc = MagicMock()
    mock_doc.id = "test-doc"
    mock_doc.pages = []
    mock_doc.metadata = MagicMock()
    mock_doc.metadata.language = "en"
    
    conversion_result = MagicMock()
    conversion_result.document = mock_doc
    converter_instance.convert.return_value = conversion_result
    
    # Test with bytes input
    pdf_bytes = b"%PDF-1.4\nTest PDF content"
    
    # Call convert_document
    with patch('papermage_docling.converter.docling_to_papermage') as mock_to_papermage:
        with patch('os.unlink') as mock_unlink:  # Mock file deletion
            mock_to_papermage.return_value = {"id": "test-doc", "metadata": {}, "pages": []}
            result = convert_document(pdf_bytes)
    
    # Verify temp file was written to and converter was called
    mock_file.write.assert_called_with(pdf_bytes)
    converter_instance.convert.assert_called_with(mock_file.name)
    assert isinstance(result, dict)


# Test end-to-end conversion and JSON output
@pytest.mark.skipif(not DOCLING_AVAILABLE, reason="Docling dependencies not available")
@patch('papermage_docling.converter.DocumentConverter')
def test_document_to_json_conversion(mock_converter, mock_docling_document, tmp_path):
    """Test end-to-end conversion and JSON serialization."""
    # Mock the DocumentConverter
    converter_instance = MagicMock()
    mock_converter.return_value = converter_instance
    
    # Mock the conversion result
    conversion_result = MagicMock()
    conversion_result.document = mock_docling_document
    converter_instance.convert.return_value = conversion_result
    
    # Convert document using patched convert_document
    with patch('papermage_docling.converter.docling_to_papermage') as mock_to_papermage:
        # Create a simple test result
        test_result = {
            "id": "test-doc",
            "metadata": {"version": "0.18.0"},
            "entities": {"words": []},
            "pages": [],
            "full_text": "This is a test document."
        }
        mock_to_papermage.return_value = test_result
        
        result = convert_document("test.pdf")
    
    # Validate JSON structure
    assert "id" in result
    assert "metadata" in result
    assert "entities" in result
    
    # Test JSON serialization
    json_path = tmp_path / "test_output.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f)
    
    # Verify file was created and can be read back
    assert json_path.exists()
    with open(json_path, "r", encoding="utf-8") as f:
        loaded_data = json.load(f)
    
    # Verify data integrity
    assert loaded_data["id"] == result["id"]
    assert loaded_data["metadata"] == result["metadata"]
    assert set(loaded_data["entities"].keys()) == set(result["entities"].keys())


# Test convert_document with a mock file path
@patch('papermage_docling.converter.DocumentConverter')
def test_convert_document_with_mock_path(mock_converter, tmp_path):
    """Test convert_document with a mock file path."""
    # Create a dummy PDF file
    pdf_path = tmp_path / "dummy.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%...dummy content...")
    
    # Mock the DocumentConverter
    converter_instance = MagicMock()
    mock_converter.return_value = converter_instance
    
    # Create mock result
    mock_doc = MagicMock()
    mock_doc.id = "test-doc"
    mock_doc.pages = []
    mock_doc.metadata = MagicMock()
    mock_doc.metadata.language = "en"
    
    conversion_result = MagicMock()
    conversion_result.document = mock_doc
    converter_instance.convert.return_value = conversion_result
    
    # Call convert_document
    with patch('papermage_docling.converter.docling_to_papermage') as mock_to_papermage:
        mock_to_papermage.return_value = {"id": "test-doc", "metadata": {}, "pages": []}
        result = convert_document(str(pdf_path))
    
    # Verify converter was called with correct options
    mock_converter.assert_called()
    assert isinstance(result, dict)


# Test docling_to_papermage with a mock doc object
def test_docling_to_papermage_with_mock():
    """Test docling_to_papermage with a mock object."""
    class MockDoc:
        def __init__(self):
            self.id = "doc-1"
            self.metadata = type("Meta", (), {"language": "en", "title": "Test", "authors": ["A"], "creation_date": "2020-01-01", "modification_date": "2020-01-02"})()
            self.pages = []
    doc = MockDoc()
    result = docling_to_papermage(doc)
    assert isinstance(result, dict)
    assert result["metadata"]["language"] == "en"
    assert result["id"] == "doc-1"


# Integration test with real PDF files
@pytest.mark.skipif(not DOCLING_AVAILABLE, reason="Docling dependencies not available")
@pytest.mark.parametrize("pdf_file", [
    ("simple", "sample1_simple.pdf"),
    ("multi_column", "sample2_multicolumn.pdf"),
])
def test_convert_real_pdf_files(pdf_file):
    """Test conversion with real PDF files from the test data directory."""
    category, filename = pdf_file
    pdf_path = TEST_SAMPLES_DIR / category / filename
    
    # Skip if the specific PDF file doesn't exist
    if not pdf_path.exists():
        pytest.skip(f"Test PDF file not found: {pdf_path}")
    
    # Convert the PDF document (no mocking for integration test)
    try:
        result = convert_document(str(pdf_path))
        
        # Basic validation of the result structure
        assert isinstance(result, dict)
        assert "id" in result
        assert "metadata" in result
        assert "pages" in result or "entities" in result
        
        # Check for some expected content based on the document
        # This is a simple validation that conversion produced some content
        if "pages" in result and result["pages"]:
            assert len(result["pages"]) > 0
        
        if "entities" in result:
            # Check if we have any common entity types
            entities = result["entities"]
            for entity_type in ["pages", "words", "tables", "figures"]:
                if entity_type in entities and entities[entity_type]:
                    assert len(entities[entity_type]) > 0
    
    except Exception as e:
        pytest.fail(f"Failed to convert real PDF file {filename}: {str(e)}") 