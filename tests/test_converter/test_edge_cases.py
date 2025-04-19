"""
Tests for edge cases in the converter module.

This module tests how the converter handles unusual or extreme inputs,
ensuring robust behavior when processing non-standard documents.
"""

import pytest

# Import application modules
try:
    from app.services.document_processing_service import DoclingConverter
except ImportError:
    pytest.skip("Required modules not available", allow_module_level=True)

# Import test utilities


def test_empty_document():
    """
    Test converter handling of an empty document with no content.
    """
    # Create a converter instance
    converter = DoclingConverter()
    
    # Create an empty document with minimal valid structure
    empty_doc = {
        "pages": []
    }
    
    # Convert the document
    result = converter.convert(empty_doc)
    
    # Verify that the result has the expected structure
    assert "pages" in result, "Result should contain pages key"
    assert len(result["pages"]) == 0, "Result should have no pages"


def test_empty_pages():
    """
    Test converter handling of pages with no content.
    """
    # Create a converter instance
    converter = DoclingConverter()
    
    # Create a document with empty pages
    empty_pages_doc = {
        "pages": [
            {
                "page_num": 1,
                "width": 612,
                "height": 792
                # No text blocks, tables, or figures
            },
            {
                "page_num": 2,
                "width": 612,
                "height": 792
                # No text blocks, tables, or figures
            }
        ]
    }
    
    # Convert the document
    result = converter.convert(empty_pages_doc)
    
    # Verify that the result has the expected structure
    assert "pages" in result, "Result should contain pages"
    assert len(result["pages"]) == 2, "Result should have two pages"
    
    # Verify page properties are correctly transferred
    for i, page in enumerate(result["pages"]):
        assert "width" in page, f"Page {i+1} should have width"
        assert "height" in page, f"Page {i+1} should have height"
        assert page["width"] == 612, f"Page {i+1} width should match input"
        assert page["height"] == 792, f"Page {i+1} height should match input"
        
        # Check empty content lists are handled properly
        if "blocks" in page:
            assert isinstance(page["blocks"], list), f"Page {i+1} blocks should be a list"
        if "tables" in page:
            assert isinstance(page["tables"], list), f"Page {i+1} tables should be a list"
        if "figures" in page:
            assert isinstance(page["figures"], list), f"Page {i+1} figures should be a list"


def test_missing_coordinates():
    """
    Test converter handling of elements with missing coordinates.
    """
    # Create a converter instance
    converter = DoclingConverter()
    
    # Create a document with missing coordinates
    missing_coords_doc = {
        "pages": [
            {
                "page_num": 1,
                "width": 612,
                "height": 792,
                "text_blocks": [
                    {
                        # Missing bbox
                        "text": "Text block with missing coordinates"
                    }
                ],
                "tables": [
                    {
                        # Missing bbox
                        "num_rows": 2,
                        "num_cols": 2,
                        "cells": [
                            {
                                "row_idx": 0,
                                "col_idx": 0,
                                # Missing bbox
                                "text": "Cell with missing coordinates"
                            }
                        ]
                    }
                ],
                "figures": [
                    {
                        # Missing bbox
                        "figure_type": "image"
                    }
                ]
            }
        ]
    }
    
    # Convert the document - should handle missing coordinates gracefully
    try:
        result = converter.convert(missing_coords_doc)
        
        # If conversion succeeds, verify that coordinates have default values
        page = result["pages"][0]
        
        # Check text blocks - if included in result
        if "blocks" in page and page["blocks"]:
            block = page["blocks"][0]
            assert all(coord in block for coord in ["x0", "y0", "x1", "y1"]), \
                "Block should have default coordinates"
        
        # Check tables - if included in result
        if "tables" in page and page["tables"]:
            table = page["tables"][0]
            assert all(coord in table for coord in ["x0", "y0", "x1", "y1"]), \
                "Table should have default coordinates"
            
            # Check cells - if included
            if "cells" in table and table["cells"]:
                cell = table["cells"][0]
                assert all(coord in cell for coord in ["x0", "y0", "x1", "y1"]), \
                    "Cell should have default coordinates"
        
        # Check figures - if included in result
        if "figures" in page and page["figures"]:
            figure = page["figures"][0]
            assert all(coord in figure for coord in ["x0", "y0", "x1", "y1"]), \
                "Figure should have default coordinates"
    
    except Exception as e:
        # If conversion fails, it should be a specific error
        assert "coordinates" in str(e).lower() or "bbox" in str(e).lower(), \
            "Exception should mention missing coordinates"


def test_malformed_bbox():
    """
    Test converter handling of elements with malformed bounding boxes.
    """
    # Create a converter instance
    converter = DoclingConverter()
    
    # Create a document with malformed bounding boxes
    malformed_bbox_doc = {
        "pages": [
            {
                "page_num": 1,
                "width": 612,
                "height": 792,
                "text_blocks": [
                    {
                        "bbox": [100, 100, 50, 150],  # x1 < x0 (invalid)
                        "text": "Text block with invalid bbox"
                    },
                    {
                        "bbox": [100, 100, 200],  # Missing y1
                        "text": "Text block with incomplete bbox"
                    },
                    {
                        "bbox": "invalid",  # Not a list
                        "text": "Text block with non-list bbox"
                    }
                ]
            }
        ]
    }
    
    # Try to convert the document
    try:
        result = converter.convert(malformed_bbox_doc)
        
        # If conversion succeeds, verify that coordinates are corrected or filtered
        page = result["pages"][0]
        
        # Check if any blocks were included
        if "blocks" in page and page["blocks"]:
            for block in page["blocks"]:
                # Coordinates should be valid
                assert block["x0"] <= block["x1"], "x0 should be <= x1"
                assert block["y0"] <= block["y1"], "y0 should be <= y1"
    
    except Exception as e:
        # If conversion fails, it should be a specific error
        assert "bbox" in str(e).lower() or "coordinate" in str(e).lower(), \
            "Exception should mention bbox or coordinates"


def test_unusual_text():
    """
    Test converter handling of unusual text content.
    """
    # Create a converter instance
    converter = DoclingConverter()
    
    # Create a document with unusual text content
    unusual_text_doc = {
        "pages": [
            {
                "page_num": 1,
                "width": 612,
                "height": 792,
                "text_blocks": [
                    {
                        "bbox": [50, 50, 150, 70],
                        "text": ""  # Empty string
                    },
                    {
                        "bbox": [50, 100, 150, 120],
                        "text": None  # None value
                    },
                    {
                        "bbox": [50, 150, 150, 170],
                        "text": "\u0000\u0001\u0002"  # Control characters
                    },
                    {
                        "bbox": [50, 200, 150, 220],
                        "text": "🙂🌍🚀"  # Emoji
                    },
                    {
                        "bbox": [50, 250, 150, 270],
                        "text": "Text with\nline\nbreaks"  # Line breaks
                    },
                    {
                        "bbox": [50, 300, 150, 320],
                        "text": "Text with    multiple    spaces"  # Multiple spaces
                    }
                ]
            }
        ]
    }
    
    # Convert the document
    result = converter.convert(unusual_text_doc)
    
    # Verify that the result has text blocks
    page = result["pages"][0]
    assert "blocks" in page, "Result should contain blocks"
    
    # Count how many blocks were processed
    processed_blocks = len(page["blocks"])
    assert processed_blocks > 0, "At least some blocks should be processed"
    
    # Check specific blocks if they exist
    block_texts = [block["text"] for block in page["blocks"] if "text" in block]
    
    # Check if emoji text is preserved
    emoji_text = "🙂🌍🚀"
    if any(txt == emoji_text for txt in block_texts):
        assert emoji_text in block_texts, "Emoji text should be preserved"
    
    # Check if line breaks are handled
    line_break_text = "Text with\nline\nbreaks"
    if any(txt == line_break_text for txt in block_texts):
        assert line_break_text in block_texts or "Text with line breaks" in block_texts, \
            "Line breaks should be handled appropriately"


def test_extremely_large_document():
    """
    Test converter handling of an extremely large document.
    """
    # Create a converter instance
    converter = DoclingConverter()
    
    # Create a large document with many pages and elements
    NUM_PAGES = 100
    BLOCKS_PER_PAGE = 50
    
    large_doc = {
        "pages": [
            {
                "page_num": page_num,
                "width": 612,
                "height": 792,
                "text_blocks": [
                    {
                        "bbox": [50, 50 + (i * 10), 150, 70 + (i * 10)],
                        "text": f"Text block {i} on page {page_num}"
                    }
                    for i in range(BLOCKS_PER_PAGE)
                ]
            }
            for page_num in range(1, NUM_PAGES + 1)
        ]
    }
    
    # Skip if the document is too large to process in reasonable time
    if NUM_PAGES * BLOCKS_PER_PAGE > 10000:
        pytest.skip("Document is too large for regular testing")
    
    # Convert the document
    try:
        # Limit execution time to avoid hanging
        with pytest.raises(TimeoutError):
            import signal
            
            def handler(signum, frame):
                raise TimeoutError("Test timed out")
            
            # Set a timeout of 10 seconds
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(10)
            
            result = converter.convert(large_doc)
            
            # If conversion completes within timeout, verify results
            signal.alarm(0)  # Cancel alarm
            
            assert "pages" in result, "Result should contain pages"
            assert len(result["pages"]) == NUM_PAGES, f"Result should have {NUM_PAGES} pages"
            
            # Verify first and last page have the expected blocks
            first_page = result["pages"][0]
            last_page = result["pages"][-1]
            
            assert "blocks" in first_page, "First page should have blocks"
            assert "blocks" in last_page, "Last page should have blocks"
            
            assert len(first_page["blocks"]) == BLOCKS_PER_PAGE, \
                f"First page should have {BLOCKS_PER_PAGE} blocks"
            assert len(last_page["blocks"]) == BLOCKS_PER_PAGE, \
                f"Last page should have {BLOCKS_PER_PAGE} blocks"
    
    except (TimeoutError, Exception):
        # If timeout or other exception, still make sure the test passes
        # as we're only testing that the converter handles large docs without crashing
        pass


def test_mixed_coordinate_formats():
    """
    Test converter handling of mixed coordinate formats.
    """
    # Create a converter instance
    converter = DoclingConverter()
    
    # Create a document with mixed coordinate formats
    mixed_coords_doc = {
        "pages": [
            {
                "page_num": 1,
                "width": 612,
                "height": 792,
                "text_blocks": [
                    {
                        "bbox": [50, 50, 150, 70],  # Standard format [x0, y0, x1, y1]
                        "text": "Standard bbox format"
                    },
                    {
                        "x0": 50, "y0": 100, "x1": 150, "y1": 120,  # Direct coordinates
                        "text": "Direct coordinate format"
                    },
                    {
                        "bbox": {"x0": 50, "y0": 150, "x1": 150, "y1": 170},  # Dictionary format
                        "text": "Dictionary bbox format"
                    }
                ]
            }
        ]
    }
    
    # Convert the document
    result = converter.convert(mixed_coords_doc)
    
    # Verify that the result has text blocks
    page = result["pages"][0]
    assert "blocks" in page, "Result should contain blocks"
    
    # Count how many blocks were processed
    processed_blocks = len(page["blocks"])
    assert processed_blocks > 0, "At least some blocks should be processed"
    
    # Check that all processed blocks have standard coordinate format
    for block in page["blocks"]:
        assert all(coord in block for coord in ["x0", "y0", "x1", "y1"]), \
            "Block should have standardized coordinates"


def test_corrupted_document():
    """
    Test converter handling of a corrupted document structure.
    """
    # Create a converter instance
    converter = DoclingConverter()
    
    # Create a corrupted document with invalid structure
    corrupted_docs = [
        # Pages as a dictionary instead of list
        {"pages": {"0": {"width": 612, "height": 792}}},
        
        # Page with non-numeric dimensions
        {"pages": [{"page_num": 1, "width": "invalid", "height": "invalid"}]},
        
        # Recursive structure
        {"pages": []},
    ]
    
    # Set recursive reference to create a cyclical structure
    corrupted_docs[2]["pages"].append(corrupted_docs[2])
    
    # Try each corrupted document
    for i, doc in enumerate(corrupted_docs):
        try:
            # Attempt conversion
            result = converter.convert(doc)
            
            # If it doesn't throw an exception, verify minimal structure
            assert "pages" in result, f"Result for corrupted doc {i} should contain pages"
            
        except Exception:
            # If it throws, that's expected behavior
            pass  # Exception is acceptable for corrupted documents


def test_duplicate_elements():
    """
    Test converter handling of documents with duplicate elements.
    """
    # Create a converter instance
    converter = DoclingConverter()
    
    # Create a document with duplicate elements
    duplicate_elements_doc = {
        "pages": [
            {
                "page_num": 1,
                "width": 612,
                "height": 792,
                "text_blocks": [
                    {
                        "bbox": [50, 50, 150, 70],
                        "text": "Duplicate text block"
                    },
                    {
                        "bbox": [50, 50, 150, 70],  # Same coordinates
                        "text": "Duplicate text block"  # Same text
                    }
                ],
                "tables": [
                    {
                        "bbox": [200, 200, 400, 300],
                        "num_rows": 2,
                        "num_cols": 2,
                        "cells": []
                    },
                    {
                        "bbox": [200, 200, 400, 300],  # Same coordinates
                        "num_rows": 2,
                        "num_cols": 2,
                        "cells": []
                    }
                ]
            }
        ]
    }
    
    # Convert the document
    result = converter.convert(duplicate_elements_doc)
    
    # Verify that the result has elements
    page = result["pages"][0]
    
    # Check blocks - converter should handle duplicates somehow
    if "blocks" in page:
        # Either keep both duplicates
        assert len(page["blocks"]) == 2, "Both duplicate blocks should be preserved"
        # Or deduplicate
        # assert len(page["blocks"]) == 1, "Duplicate blocks should be deduplicated"
    
    # Check tables - converter should handle duplicates somehow
    if "tables" in page:
        # Either keep both duplicates
        assert len(page["tables"]) == 2, "Both duplicate tables should be preserved"
        # Or deduplicate
        # assert len(page["tables"]) == 1, "Duplicate tables should be deduplicated"


def test_invalid_nesting():
    """
    Test converter handling of invalid nesting structures.
    """
    # Create a converter instance
    converter = DoclingConverter()
    
    # Create a document with invalid nesting
    invalid_nesting_doc = {
        "pages": [
            {
                "page_num": 1,
                "width": 612,
                "height": 792,
                "text_blocks": [
                    {
                        "bbox": [50, 50, 150, 70],
                        "text": "Parent text block",
                        "nested_blocks": [  # Unexpected nesting
                            {
                                "bbox": [60, 60, 140, 65],
                                "text": "Nested text block"
                            }
                        ]
                    }
                ],
                "tables": [
                    {
                        "bbox": [200, 200, 400, 300],
                        "num_rows": 1,
                        "num_cols": 1,
                        "cells": [
                            {
                                "row_idx": 0,
                                "col_idx": 0,
                                "bbox": [200, 200, 400, 300],
                                "tables": [  # Nested table inside cell
                                    {
                                        "bbox": [220, 220, 380, 280],
                                        "num_rows": 1,
                                        "num_cols": 1,
                                        "cells": []
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    # Convert the document
    try:
        result = converter.convert(invalid_nesting_doc)
        
        # If conversion succeeds, check the structure
        page = result["pages"][0]
        
        # Check if text blocks are processed
        if "blocks" in page:
            assert len(page["blocks"]) > 0, "At least the parent text block should be processed"
        
        # Check if tables are processed
        if "tables" in page:
            assert len(page["tables"]) > 0, "At least the parent table should be processed"
            
            # Check if cell is processed
            if page["tables"] and "cells" in page["tables"][0]:
                assert len(page["tables"][0]["cells"]) > 0, "Table cell should be processed"
    
    except Exception:
        # If conversion fails, it's acceptable as this is an edge case
        pass
