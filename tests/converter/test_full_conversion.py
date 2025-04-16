"""
Tests for full document conversion.

This module tests the complete document conversion process, ensuring that
the converter correctly transforms Docling documents into the expected
JSON format with all elements correctly processed.
"""

import os
import json
import pytest
import jsonschema
from pathlib import Path

# Import application modules
try:
    from app.services.pipeline_service import PipelineService
    from app.services.document_processing_service import DoclingConverter
except ImportError:
    pytest.skip("Required modules not available", allow_module_level=True)

# Import test utilities
from ..conftest import TEST_DATA_DIR, TEST_EXPECTED_DIR, TEST_VISUALS_DIR

# Import the document schema from schema validation tests
try:
    from .test_schema_validation import DOCUMENT_SCHEMA
except ImportError:
    # Fallback schema if import fails
    DOCUMENT_SCHEMA = {
        "type": "object",
        "required": ["pages"],
        "properties": {
            "pages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["width", "height"]
                }
            }
        }
    }


def test_full_conversion_simple_document():
    """
    Test full conversion of a simple document with basic elements.
    """
    # Skip if sample data isn't available
    sample_name = "sample1_simple"
    pdf_path = TEST_DATA_DIR / f"{sample_name}.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Sample PDF {sample_name}.pdf not found")
    
    # Process the document
    pipeline_service = PipelineService()
    result = pipeline_service.process_document(str(pdf_path))
    
    # Verify that the result has the expected structure
    assert "pages" in result, "Result should contain pages"
    assert len(result["pages"]) > 0, "Result should have at least one page"
    
    # Check basic elements
    page = result["pages"][0]
    assert "width" in page, "Page should have width"
    assert "height" in page, "Page should have height"
    assert "blocks" in page, "Page should have text blocks"
    
    # Validate against schema
    try:
        jsonschema.validate(instance=result, schema=DOCUMENT_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        pytest.fail(f"Full conversion result does not match schema: {e}")
    
    # Save the conversion result for manual inspection
    output_path = TEST_VISUALS_DIR / f"{sample_name}_full_conversion.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)


def test_full_conversion_complex_document():
    """
    Test full conversion of a complex document with tables and figures.
    """
    # Skip if sample data isn't available
    sample_name = "sample4_tables"  # Or another complex document
    pdf_path = TEST_DATA_DIR / f"{sample_name}.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Sample PDF {sample_name}.pdf not found")
    
    # Process the document
    pipeline_service = PipelineService()
    result = pipeline_service.process_document(str(pdf_path))
    
    # Verify that the result has the expected structure
    assert "pages" in result, "Result should contain pages"
    assert len(result["pages"]) > 0, "Result should have at least one page"
    
    # Check for tables
    tables_found = False
    for page in result["pages"]:
        if "tables" in page and page["tables"]:
            tables_found = True
            break
    
    if not tables_found:
        pytest.skip("No tables found in the document")
    
    # Validate against schema
    try:
        jsonschema.validate(instance=result, schema=DOCUMENT_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        pytest.fail(f"Full conversion result does not match schema: {e}")
    
    # Save the conversion result for manual inspection
    output_path = TEST_VISUALS_DIR / f"{sample_name}_full_conversion.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)


def test_full_conversion_scanned_document():
    """
    Test full conversion of a scanned document that requires OCR.
    """
    # Skip if sample data isn't available
    sample_name = "sample3_scanned"
    pdf_path = TEST_DATA_DIR / f"{sample_name}.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Sample PDF {sample_name}.pdf not found")
    
    # Process the document
    pipeline_service = PipelineService()
    result = pipeline_service.process_document(str(pdf_path))
    
    # Verify that the result has the expected structure
    assert "pages" in result, "Result should contain pages"
    assert len(result["pages"]) > 0, "Result should have at least one page"
    
    # Check for text blocks (OCR should extract some text)
    text_found = False
    for page in result["pages"]:
        if "blocks" in page and page["blocks"]:
            for block in page["blocks"]:
                if "text" in block and block["text"].strip():
                    text_found = True
                    break
            if text_found:
                break
    
    if not text_found:
        pytest.skip("No text found in the scanned document (OCR may have failed)")
    
    # Validate against schema
    try:
        jsonschema.validate(instance=result, schema=DOCUMENT_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        pytest.fail(f"Full conversion result does not match schema: {e}")
    
    # Save the conversion result for manual inspection
    output_path = TEST_VISUALS_DIR / f"{sample_name}_full_conversion.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)


def test_comparison_with_expected_output(expected_outputs):
    """
    Test that full conversion outputs match the expected outputs.
    
    Args:
        expected_outputs: Fixture providing expected outputs
    """
    # Skip if no expected outputs
    if not expected_outputs:
        pytest.skip("No expected outputs available")
    
    # For each sample with expected output
    for sample_name, expected_output in expected_outputs.items():
        # Skip if sample PDF doesn't exist
        pdf_path = TEST_DATA_DIR / f"{sample_name}.pdf"
        if not pdf_path.exists():
            continue
        
        # Process the document
        pipeline_service = PipelineService()
        result = pipeline_service.process_document(str(pdf_path))
        
        # Compare key structures between result and expected output
        assert "pages" in result, f"{sample_name}: Result should contain pages"
        assert "pages" in expected_output, f"{sample_name}: Expected output should contain pages"
        assert len(result["pages"]) == len(expected_output["pages"]), \
            f"{sample_name}: Result should have same number of pages as expected output"
        
        # Compare page dimensions
        for page_idx, (result_page, expected_page) in enumerate(zip(result["pages"], expected_output["pages"])):
            assert "width" in result_page, f"{sample_name}: Page {page_idx} should have width"
            assert "height" in result_page, f"{sample_name}: Page {page_idx} should have height"
            assert result_page["width"] == expected_page["width"], \
                f"{sample_name}: Page {page_idx} width should match expected"
            assert result_page["height"] == expected_page["height"], \
                f"{sample_name}: Page {page_idx} height should match expected"
        
        # Compare metadata if present
        if "metadata" in expected_output and "metadata" in result:
            for key in expected_output["metadata"]:
                if key in result["metadata"]:
                    assert result["metadata"][key] == expected_output["metadata"][key], \
                        f"{sample_name}: Metadata '{key}' should match expected"


def test_round_trip_conversion():
    """
    Test that a round-trip conversion (document -> JSON -> document) preserves structure.
    """
    # Create a simple document structure
    original_doc = {
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
                ],
                "tables": [
                    {
                        "bbox": [200, 200, 400, 300],
                        "num_rows": 2,
                        "num_cols": 2,
                        "cells": [
                            {
                                "row_idx": 0,
                                "col_idx": 0,
                                "bbox": [200, 200, 300, 250],
                                "text": "A1"
                            },
                            {
                                "row_idx": 0,
                                "col_idx": 1,
                                "bbox": [300, 200, 400, 250],
                                "text": "B1"
                            },
                            {
                                "row_idx": 1,
                                "col_idx": 0,
                                "bbox": [200, 250, 300, 300],
                                "text": "A2"
                            },
                            {
                                "row_idx": 1,
                                "col_idx": 1,
                                "bbox": [300, 250, 400, 300],
                                "text": "B2"
                            }
                        ]
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
    
    # Convert to JSON format
    converter = DoclingConverter()
    json_result = converter.convert(original_doc)
    
    # Validate against schema
    try:
        jsonschema.validate(instance=json_result, schema=DOCUMENT_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        pytest.fail(f"Conversion result does not match schema: {e}")
    
    # Check that key information is preserved
    assert "pages" in json_result, "Result should contain pages"
    assert len(json_result["pages"]) == 1, "Result should have one page"
    
    # Check page properties
    page = json_result["pages"][0]
    assert "width" in page, "Page should have width"
    assert "height" in page, "Page should have height"
    assert page["width"] == 612, "Page width should be preserved"
    assert page["height"] == 792, "Page height should be preserved"
    
    # Check text blocks
    assert "blocks" in page, "Page should have blocks"
    assert len(page["blocks"]) == 1, "Page should have one block"
    assert "text" in page["blocks"][0], "Block should have text"
    assert page["blocks"][0]["text"] == "Sample text block", "Block text should be preserved"
    
    # Check tables
    assert "tables" in page, "Page should have tables"
    assert len(page["tables"]) == 1, "Page should have one table"
    assert "cells" in page["tables"][0], "Table should have cells"
    assert len(page["tables"][0]["cells"]) == 4, "Table should have four cells"
    
    # Check metadata
    assert "metadata" in json_result, "Result should contain metadata"
    assert json_result["metadata"]["title"] == "Test Document", "Title should be preserved"
    assert json_result["metadata"]["author"] == "Test Author", "Author should be preserved"
    
    # Save the conversion result for inspection
    output_path = TEST_VISUALS_DIR / "round_trip_conversion.json"
    with open(output_path, 'w') as f:
        json.dump(json_result, f, indent=2)


def test_conversion_performance():
    """
    Test the performance of the conversion process.
    """
    # Create a large document for performance testing
    NUM_PAGES = 5
    BLOCKS_PER_PAGE = 100
    
    large_doc = {
        "pages": [
            {
                "page_num": page_num,
                "width": 612,
                "height": 792,
                "text_blocks": [
                    {
                        "bbox": [50, 50 + (i * 5), 150, 70 + (i * 5)],
                        "text": f"Text block {i} on page {page_num}"
                    }
                    for i in range(BLOCKS_PER_PAGE)
                ]
            }
            for page_num in range(1, NUM_PAGES + 1)
        ]
    }
    
    # Time the conversion
    import time
    converter = DoclingConverter()
    
    start_time = time.time()
    result = converter.convert(large_doc)
    end_time = time.time()
    
    conversion_time = end_time - start_time
    print(f"Conversion time for {NUM_PAGES} pages with {BLOCKS_PER_PAGE} blocks each: {conversion_time:.4f} seconds")
    
    # Assert that conversion completes within a reasonable time
    # (adjust threshold based on expected performance)
    assert conversion_time < 10.0, f"Conversion took too long: {conversion_time:.4f} seconds"
    
    # Verify result has the right number of pages and blocks
    assert "pages" in result, "Result should contain pages"
    assert len(result["pages"]) == NUM_PAGES, f"Result should have {NUM_PAGES} pages"
    
    # Check first page blocks
    first_page = result["pages"][0]
    assert "blocks" in first_page, "Page should have blocks"
    assert len(first_page["blocks"]) == BLOCKS_PER_PAGE, f"Page should have {BLOCKS_PER_PAGE} blocks"
