"""
Tests for the DoclingToPaperMageConverter class.

This module contains unit tests for the DoclingToPaperMageConverter class
which converts between Docling document formats and PaperMage JSON.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Import our document structure
from papermage_docling.converters.document import Document, Entity, Span, Box
from papermage_docling.converters.docling_to_papermage_converter import DoclingToPaperMageConverter

# Skip tests if Docling dependencies are not available
try:
    from docling_core.types import DoclingDocument
    from docling_parse.pdf_parser import PdfDocument
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False


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
    
    return mock_doc


@pytest.fixture
def mock_docling_document():
    """Create a mock DoclingDocument for testing."""
    mock_doc = MagicMock(spec=DoclingDocument)
    
    # Set basic attributes
    mock_doc.text = "This is a test document."
    mock_doc.title = "Test Document"
    mock_doc.metadata = {"author": "Test Author", "language": "en"}
    
    # Mock page
    mock_page = MagicMock()
    mock_page.width = 612
    mock_page.height = 792
    
    # Mock text item
    mock_text_item = MagicMock()
    mock_text_item.text = "This is a paragraph."
    mock_text_item.category = "paragraph"
    mock_text_item.bbox.x0 = 50
    mock_text_item.bbox.y0 = 100
    mock_text_item.bbox.x1 = 500
    mock_text_item.bbox.y1 = 120
    
    # Set up structure
    mock_page.content = [mock_text_item]
    mock_doc.pages = [mock_page]
    
    return mock_doc


# Test PdfDocument conversion
@pytest.mark.skipif(not DOCLING_AVAILABLE, reason="Docling dependencies not available")
def test_convert_pdf_document(mock_pdf_document):
    """Test conversion of PdfDocument to PaperMage format."""
    # Convert the document
    result = DoclingToPaperMageConverter.convert_pdf_document(mock_pdf_document)
    
    # Validate basic structure
    assert isinstance(result, Document)
    assert "This is a test line." in result.symbols
    assert "test" in result.symbols
    
    # Check entity layers
    assert "pages" in result.entities
    assert "rows" in result.entities
    assert "tokens" in result.entities
    assert "words" in result.entities
    
    # Check metadata
    assert result.metadata["filename"] == "test.pdf"
    assert result.metadata["num_pages"] == 1
    assert result.metadata["version"] == "0.1.0"


# Test DoclingDocument conversion
@pytest.mark.skipif(not DOCLING_AVAILABLE, reason="Docling dependencies not available")
def test_convert_docling_document(mock_docling_document):
    """Test conversion of DoclingDocument to PaperMage format."""
    # Convert the document
    result = DoclingToPaperMageConverter.convert_docling_document(mock_docling_document)
    
    # Validate basic structure
    assert isinstance(result, Document)
    assert "This is a paragraph." in result.symbols
    
    # Check entity layers present
    assert "pages" in result.entities
    assert "blocks" in result.entities
    assert "paragraphs" in result.entities
    
    # Check metadata
    assert result.metadata["source"] == "docling"
    assert result.metadata["version"] == "0.18.0"  # PaperMage v0.18+ compatibility
    assert result.metadata["author"] == "Test Author"
    assert result.metadata["language"] == "en"
    assert result.metadata["title"] == "Test Document"


# Test JSON format validation
def test_validate_papermage_format():
    """Test validation of PaperMage document format."""
    # Create a valid document
    doc = Document(
        symbols="Test document",
        metadata={"version": "0.18.0"},
        entities={
            "pages": [
                Entity(
                    spans=[Span(start=0, end=12)],
                    boxes=[Box(x0=0, y0=0, x1=100, y1=100, page=0)],
                    text="Test document"
                )
            ]
        }
    )
    
    # Validate format
    assert DoclingToPaperMageConverter.validate_papermage_format(doc) is True
    
    # Test invalid document (missing required fields)
    invalid_doc = Document(symbols="")
    with pytest.raises(ValueError):
        invalid_doc.entities = None
        DoclingToPaperMageConverter.validate_papermage_format(invalid_doc)


# Test end-to-end conversion and JSON output
@pytest.mark.skipif(not DOCLING_AVAILABLE, reason="Docling dependencies not available")
def test_document_to_json_conversion(mock_docling_document, tmp_path):
    """Test end-to-end conversion and JSON serialization."""
    # Convert document
    papermage_doc = DoclingToPaperMageConverter.convert_docling_document(mock_docling_document)
    
    # Convert to JSON
    json_data = papermage_doc.to_json()
    
    # Validate JSON structure
    assert "symbols" in json_data
    assert "entities" in json_data
    assert "metadata" in json_data
    
    # Test JSON serialization
    json_path = tmp_path / "test_output.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f)
    
    # Verify file was created and can be read back
    assert json_path.exists()
    with open(json_path, "r", encoding="utf-8") as f:
        loaded_data = json.load(f)
    
    # Verify data integrity
    assert loaded_data["symbols"] == json_data["symbols"]
    assert loaded_data["metadata"] == json_data["metadata"]
    assert set(loaded_data["entities"].keys()) == set(json_data["entities"].keys()) 