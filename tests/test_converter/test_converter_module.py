"""
Tests for the converter module that transforms Docling output to the expected JSON format.

This module verifies the functionality of the converter that transforms 
raw Docling document parsing output into the structured JSON format 
expected by downstream systems.
"""

import json

import pytest

# Import application modules
try:
    from app.services.document_processing_service import DoclingConverter
    from app.services.pipeline_service import PipelineService
except ImportError:
    pytest.skip("Required modules not available", allow_module_level=True)

# Import test utilities
from ..conftest import TEST_DATA_DIR, TEST_VISUALS_DIR


def test_converter_initialization():
    """
    Test that the converter module initializes correctly with default parameters.
    """
    # Create a converter instance
    converter = DoclingConverter()
    
    # Verify that the converter has the required attributes and methods
    assert hasattr(converter, "convert"), "Converter should have convert method"
    
    # Check if the converter has configuration attributes
    assert hasattr(converter, "config") or hasattr(converter, "options"), \
        "Converter should have configuration options"


def test_converter_basic_functionality():
    """
    Test the basic functionality of the converter with a simple document.
    """
    # Create a converter instance
    converter = DoclingConverter()
    
    # Create a simple Docling document structure
    docling_doc = {
        "pages": [
            {
                "page_num": 1,
                "width": 612,
                "height": 792,
                "text_blocks": [
                    {
                        "bbox": [50, 50, 150, 70],
                        "text": "Sample text block"
                    }
                ]
            }
        ],
        "metadata": {
            "title": "Test Document",
            "author": "Test Author",
            "num_pages": 1
        }
    }
    
    # Convert the document
    result = converter.convert(docling_doc)
    
    # Verify the basic structure of the result
    assert "pages" in result, "Result should contain pages"
    assert len(result["pages"]) == 1, "Result should have one page"
    
    # Verify page properties are correctly transferred
    page = result["pages"][0]
    assert "width" in page, "Page should have width"
    assert "height" in page, "Page should have height"
    assert page["width"] == 612, "Page width should match input"
    assert page["height"] == 792, "Page height should match input"
    
    # Verify metadata
    assert "metadata" in result, "Result should contain metadata"
    assert result["metadata"]["title"] == "Test Document", "Title should match input"
    assert result["metadata"]["author"] == "Test Author", "Author should match input"


def test_converter_text_block_transformation():
    """
    Test that text blocks are correctly transformed by the converter.
    """
    # Create a converter instance
    converter = DoclingConverter()
    
    # Create a Docling document with text blocks
    docling_doc = {
        "pages": [
            {
                "page_num": 1,
                "width": 612,
                "height": 792,
                "text_blocks": [
                    {
                        "bbox": [50, 50, 150, 70],
                        "text": "First text block"
                    },
                    {
                        "bbox": [50, 100, 150, 120],
                        "text": "Second text block"
                    }
                ]
            }
        ]
    }
    
    # Convert the document
    result = converter.convert(docling_doc)
    
    # Verify text blocks transformation
    page = result["pages"][0]
    assert "blocks" in page, "Page should have blocks"
    assert len(page["blocks"]) == 2, "Page should have two blocks"
    
    # Check coordinates
    block = page["blocks"][0]
    assert "x0" in block, "Block should have x0 coordinate"
    assert "y0" in block, "Block should have y0 coordinate"
    assert "x1" in block, "Block should have x1 coordinate"
    assert "y1" in block, "Block should have y1 coordinate"
    assert block["x0"] == 50, "Block x0 should match input"
    assert block["y0"] == 50, "Block y0 should match input"
    assert block["x1"] == 150, "Block x1 should match input"
    assert block["y1"] == 70, "Block y1 should match input"
    
    # Check text content
    assert "text" in block, "Block should have text"
    assert block["text"] == "First text block", "Block text should match input"


def test_converter_table_transformation():
    """
    Test that tables are correctly transformed by the converter.
    """
    # Create a converter instance
    converter = DoclingConverter()
    
    # Create a Docling document with tables
    docling_doc = {
        "pages": [
            {
                "page_num": 1,
                "width": 612,
                "height": 792,
                "tables": [
                    {
                        "bbox": [100, 100, 300, 200],
                        "num_rows": 2,
                        "num_cols": 2,
                        "cells": [
                            {
                                "row_idx": 0,
                                "col_idx": 0,
                                "bbox": [100, 100, 200, 150],
                                "text": "A1"
                            },
                            {
                                "row_idx": 0,
                                "col_idx": 1,
                                "bbox": [200, 100, 300, 150],
                                "text": "B1"
                            },
                            {
                                "row_idx": 1,
                                "col_idx": 0,
                                "bbox": [100, 150, 200, 200],
                                "text": "A2"
                            },
                            {
                                "row_idx": 1,
                                "col_idx": 1,
                                "bbox": [200, 150, 300, 200],
                                "text": "B2"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    # Convert the document
    result = converter.convert(docling_doc)
    
    # Verify tables transformation
    page = result["pages"][0]
    assert "tables" in page, "Page should have tables"
    assert len(page["tables"]) == 1, "Page should have one table"
    
    # Check table properties
    table = page["tables"][0]
    assert "rows" in table, "Table should have rows count"
    assert "cols" in table, "Table should have columns count"
    assert table["rows"] == 2, "Table should have 2 rows"
    assert table["cols"] == 2, "Table should have 2 columns"
    
    # Check table coordinates
    assert "x0" in table, "Table should have x0 coordinate"
    assert "y0" in table, "Table should have y0 coordinate"
    assert "x1" in table, "Table should have x1 coordinate"
    assert "y1" in table, "Table should have y1 coordinate"
    assert table["x0"] == 100, "Table x0 should match input"
    assert table["y0"] == 100, "Table y0 should match input"
    assert table["x1"] == 300, "Table x1 should match input"
    assert table["y1"] == 200, "Table y1 should match input"
    
    # Check cells
    assert "cells" in table, "Table should have cells"
    assert len(table["cells"]) == 4, "Table should have 4 cells"
    
    # Check first cell
    cell = table["cells"][0]
    assert "row" in cell, "Cell should have row index"
    assert "col" in cell, "Cell should have column index"
    assert "text" in cell, "Cell should have text"
    assert cell["row"] == 0, "Cell row should match input"
    assert cell["col"] == 0, "Cell column should match input"
    assert cell["text"] == "A1", "Cell text should match input"


def test_converter_figure_transformation():
    """
    Test that figures are correctly transformed by the converter.
    """
    # Create a converter instance
    converter = DoclingConverter()
    
    # Create a Docling document with figures
    docling_doc = {
        "pages": [
            {
                "page_num": 1,
                "width": 612,
                "height": 792,
                "figures": [
                    {
                        "bbox": [100, 300, 300, 400],
                        "figure_type": "image",
                        "caption_text": "Sample Figure Caption"
                    }
                ]
            }
        ]
    }
    
    # Convert the document
    result = converter.convert(docling_doc)
    
    # Verify figures transformation
    page = result["pages"][0]
    assert "figures" in page, "Page should have figures"
    assert len(page["figures"]) == 1, "Page should have one figure"
    
    # Check figure properties
    figure = page["figures"][0]
    assert "x0" in figure, "Figure should have x0 coordinate"
    assert "y0" in figure, "Figure should have y0 coordinate"
    assert "x1" in figure, "Figure should have x1 coordinate"
    assert "y1" in figure, "Figure should have y1 coordinate"
    assert figure["x0"] == 100, "Figure x0 should match input"
    assert figure["y0"] == 300, "Figure y0 should match input"
    assert figure["x1"] == 300, "Figure x1 should match input"
    assert figure["y1"] == 400, "Figure y1 should match input"
    
    # Check figure type
    assert any(key in figure for key in ["type", "image_type", "content_type"]), \
        "Figure should have type information"
    
    # Check caption
    if "caption_text" in figure:
        assert figure["caption_text"] == "Sample Figure Caption", \
            "Figure caption should match input"
    elif "caption" in figure and isinstance(figure["caption"], dict) and "text" in figure["caption"]:
        assert figure["caption"]["text"] == "Sample Figure Caption", \
            "Figure caption text should match input"
    elif "caption" in figure and isinstance(figure["caption"], str):
        assert figure["caption"] == "Sample Figure Caption", \
            "Figure caption should match input"


def test_converter_with_complex_input():
    """
    Test the converter with more complex and realistic input.
    """
    # Skip this test if real sample data isn't available
    sample_name = "sample1_simple"
    pdf_path = TEST_DATA_DIR / f"{sample_name}.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Sample PDF {sample_name}.pdf not found")
    
    # Use PipelineService to get raw Docling output
    pipeline_service = PipelineService()
    # Assuming get_raw_docling_output is available, otherwise use process_document
    try:
        docling_output = pipeline_service.get_raw_docling_output(str(pdf_path))
    except (AttributeError, TypeError):
        pytest.skip("Pipeline service doesn't support getting raw Docling output")
    
    # Create converter and transform the output
    converter = DoclingConverter()
    result = converter.convert(docling_output)
    
    # Verify that the result has the expected structure
    assert "pages" in result, "Result should contain pages"
    assert len(result["pages"]) > 0, "Result should have at least one page"
    
    # Save the conversion result for manual inspection
    output_path = TEST_VISUALS_DIR / f"{sample_name}_conversion_result.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)


def test_converter_rtl_support():
    """
    Test that the converter correctly handles right-to-left text.
    """
    # Create a converter instance
    converter = DoclingConverter()
    
    # Create a Docling document with RTL text
    docling_doc = {
        "pages": [
            {
                "page_num": 1,
                "width": 612,
                "height": 792,
                "text_blocks": [
                    {
                        "bbox": [50, 50, 150, 70],
                        "text": "مرحبا بالعالم",  # "Hello World" in Arabic
                        "direction": "rtl"
                    }
                ]
            }
        ]
    }
    
    # Convert the document
    result = converter.convert(docling_doc)
    
    # Verify RTL text handling
    page = result["pages"][0]
    block = page["blocks"][0]
    
    # Check text content is preserved
    assert block["text"] == "مرحبا بالعالم", "RTL text should be preserved"
    
    # Check if direction is preserved in the output
    # This depends on the specific converter implementation
    if "direction" in block:
        assert block["direction"] == "rtl", "RTL direction should be preserved"


def test_converter_error_handling():
    """
    Test that the converter handles invalid input gracefully.
    """
    # Create a converter instance
    converter = DoclingConverter()
    
    # Test with None input
    with pytest.raises(Exception):
        converter.convert(None)
    
    # Test with empty dictionary
    with pytest.raises(Exception):
        converter.convert({})
    
    # Test with invalid structure
    invalid_doc = {"invalid_key": "invalid_value"}
    with pytest.raises(Exception):
        converter.convert(invalid_doc)


def test_converter_configuration():
    """
    Test that the converter can be configured with different options.
    """
    # Skip if the converter doesn't support configuration
    try:
        converter = DoclingConverter(include_metadata=False)
    except TypeError:
        pytest.skip("Converter doesn't support configuration")
    
    # Create a simple Docling document
    docling_doc = {
        "pages": [
            {
                "page_num": 1,
                "width": 612,
                "height": 792
            }
        ],
        "metadata": {
            "title": "Test Document"
        }
    }
    
    # Convert without metadata
    result = converter.convert(docling_doc)
    
    # Check that metadata is not included
    assert "metadata" not in result or not result["metadata"], \
        "Result should not contain metadata when include_metadata=False"
    
    # Create a converter with different options
    converter = DoclingConverter(include_metadata=True)
    
    # Convert with metadata
    result = converter.convert(docling_doc)
    
    # Check that metadata is included
    assert "metadata" in result, "Result should contain metadata when include_metadata=True"
    assert result["metadata"]["title"] == "Test Document", "Metadata should match input"
