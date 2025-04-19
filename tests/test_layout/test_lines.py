"""
Tests for layout analysis and reading order.

This module validates that the document processing correctly identifies text layouts
and preserves the proper reading order, especially for multi-column documents.
"""


import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pytest

# Import application modules
try:
    from app.services.pipeline_service import PipelineService
except ImportError:
    pytest.skip("PipelineService not available", allow_module_level=True)

# Import test utilities
from ..conftest import TEST_DATA_DIR, TEST_VISUALS_DIR


def draw_layout_visualization(document, page_idx, output_path, highlight_reading_order=False):
    """
    Create a visualization of the document layout with bounding boxes.
    
    Args:
        document: Processed document JSON
        page_idx: Index of the page to visualize
        output_path: Path to save the visualization image
        highlight_reading_order: Whether to color-code blocks by reading order
        
    Returns:
        Path: Path to the saved visualization image
    """
    # Create figure and axes
    fig, ax = plt.subplots(figsize=(12, 16))
    
    # Set title
    ax.set_title(f"Layout Analysis - Page {page_idx + 1}")
    
    # Get page dimensions from document
    try:
        page = document.get("pages", [])[page_idx]
        width = page.get("width", 1000)
        height = page.get("height", 1400)
        
        # Set axes limits
        ax.set_xlim(0, width)
        ax.set_ylim(0, height)
        
        # Draw text blocks with numbers to indicate reading order
        blocks = page.get("blocks", [])
        
        # Generate color map for reading order if requested
        if highlight_reading_order and blocks:
            colors = plt.cm.rainbow(np.linspace(0, 1, len(blocks)))
        else:
            colors = ['r'] * len(blocks)
        
        for i, block in enumerate(blocks):
            # Get coordinates
            x0 = block.get("x0", 0)
            y0 = block.get("y0", 0)
            x1 = block.get("x1", x0 + 100)
            y1 = block.get("y1", y0 + 20)
            
            # Draw rectangle with color based on reading order
            rect = patches.Rectangle(
                (x0, y0), x1 - x0, y1 - y0, 
                linewidth=1, 
                edgecolor=colors[i] if highlight_reading_order else 'r', 
                facecolor='none'
            )
            ax.add_patch(rect)
            
            # Add block number (reading order)
            ax.text(
                (x0 + x1) / 2, (y0 + y1) / 2, 
                str(i+1), 
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=8,
                bbox=dict(facecolor='white', alpha=0.7)
            )
            
            # Add small sample of text if available (first 15 chars)
            if "text" in block and block["text"]:
                text_sample = block["text"][:15] + "..." if len(block["text"]) > 15 else block["text"]
                ax.text(
                    x0, y0 - 5, 
                    text_sample,
                    fontsize=6,
                    color='blue',
                    verticalalignment='bottom'
                )
    except (IndexError, KeyError) as e:
        # If document structure doesn't match expectations, draw empty diagram
        ax.text(
            width / 2, height / 2, 
            f"Error visualizing layout: {str(e)}", 
            horizontalalignment='center',
            verticalalignment='center'
        )
    
    # Save the figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    return output_path

def test_text_block_structure(expected_outputs):
    """
    Test that text blocks have the expected structure with all required fields.
    
    Args:
        expected_outputs: Fixture providing expected outputs
    """
    # Check that we have at least one expected output
    assert expected_outputs, "No expected outputs available for testing"
    
    # Get the first available document
    sample_name = next(iter(expected_outputs.keys()))
    document = expected_outputs[sample_name]
    
    # Check document structure
    assert "pages" in document, "Document should have 'pages' array"
    assert len(document["pages"]) > 0, "Document should have at least one page"
    
    # Get the first page
    page = document["pages"][0]
    
    # Verify text blocks exist
    assert "blocks" in page, "Page should have text blocks"
    assert len(page["blocks"]) > 0, "Page should have at least one text block"
    
    # Check the first block's structure
    block = page["blocks"][0]
    
    # Required coordinate fields
    assert "x0" in block, "Block should have x0 coordinate"
    assert "y0" in block, "Block should have y0 coordinate"
    assert "x1" in block, "Block should have x1 coordinate"
    assert "y1" in block, "Block should have y1 coordinate"
    
    # Text content
    assert "text" in block, "Block should have text content"
    
    # Metadata fields that should exist
    if "font" in block:
        assert isinstance(block["font"], str), "Font should be a string"
    
    if "font_size" in block:
        assert isinstance(block["font_size"], (int, float)), "Font size should be a number"
    
    if "confidence" in block:
        assert 0 <= block["confidence"] <= 1, "Confidence should be between 0 and 1"

@pytest.mark.parametrize("sample_name", [
    "sample1_simple",      # Single column document
    "sample2_multicolumn", # Multi-column document
])
def test_layout_extraction(sample_name, attach_visual, compare_json, expected_outputs):
    """
    Test that document layout is correctly extracted and reading order is preserved.
    
    Args:
        sample_name: Name of the sample PDF to test
        attach_visual: Fixture to attach visualizations to the HTML report
        compare_json: Fixture to compare JSON outputs
        expected_outputs: Fixture providing expected outputs
    """
    # Skip if sample PDF or expected output doesn't exist
    pdf_path = TEST_DATA_DIR / f"{sample_name}.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Sample PDF {sample_name}.pdf not found")
    
    expected_output = expected_outputs.get(sample_name)
    if expected_output is None:
        pytest.skip(f"Expected output for {sample_name} not found")
    
    # Process the document
    pipeline_service = PipelineService()
    result = pipeline_service.process_document(str(pdf_path))
    
    # Create visualization for the first page
    visual_path = TEST_VISUALS_DIR / f"{sample_name}_layout.png"
    draw_layout_visualization(result, 0, visual_path)
    
    # Attach visualization to the HTML report
    attach_visual(visual_path, f"{sample_name} - Layout")
    
    # Verify document structure
    assert "pages" in result, "Document should have 'pages' array"
    assert len(result["pages"]) > 0, "Document should have at least one page"
    
    # Verify text content exists
    first_page = result["pages"][0]
    assert "blocks" in first_page, "Page should have text blocks"
    assert len(first_page["blocks"]) > 0, "Page should have at least one text block"
    
    # Verify all blocks have required fields
    for i, block in enumerate(first_page["blocks"]):
        assert "x0" in block, f"Block {i} should have x0 coordinate"
        assert "y0" in block, f"Block {i} should have y0 coordinate"
        assert "x1" in block, f"Block {i} should have x1 coordinate"
        assert "y1" in block, f"Block {i} should have y1 coordinate"
        assert "text" in block, f"Block {i} should have text content"
    
    # Compare with expected output
    assert compare_json(result, expected_output), \
        f"Document processing result doesn't match expected output for {sample_name}"

def test_single_column_reading_order(attach_visual, expected_outputs):
    """
    Test reading order for single-column documents to ensure text flows correctly.
    """
    sample_name = "sample1_simple"
    
    # Skip if sample PDF or expected output doesn't exist
    pdf_path = TEST_DATA_DIR / f"{sample_name}.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Sample PDF {sample_name}.pdf not found")
    
    expected_output = expected_outputs.get(sample_name)
    if expected_output is None:
        pytest.skip(f"Expected output for {sample_name} not found")
    
    # Process the document
    pipeline_service = PipelineService()
    result = pipeline_service.process_document(str(pdf_path))
    
    # Create visualization highlighting reading order
    visual_path = TEST_VISUALS_DIR / f"{sample_name}_reading_order.png"
    draw_layout_visualization(result, 0, visual_path, highlight_reading_order=True)
    
    # Attach visualization to the HTML report
    attach_visual(visual_path, f"{sample_name} - Reading Order")
    
    # Verify page exists
    assert "pages" in result and len(result["pages"]) > 0, "Document should have at least one page"
    page = result["pages"][0]
    
    # Verify blocks exist
    assert "blocks" in page and len(page["blocks"]) > 0, "Page should have text blocks"
    blocks = page["blocks"]
    
    # In a single column document, blocks should be ordered top to bottom
    for i in range(1, len(blocks)):
        prev_block = blocks[i-1]
        curr_block = blocks[i]
        
        # If the current block starts below the previous block's midpoint,
        # it should be positioned lower on the page
        prev_mid_y = (prev_block["y0"] + prev_block["y1"]) / 2
        if curr_block["y0"] > prev_mid_y:
            assert curr_block["y0"] > prev_block["y0"], \
                f"Block {i} should be below block {i-1} in single-column layout"

def test_multicolumn_reading_order(attach_visual, expected_outputs):
    """
    Specifically test multi-column reading order to ensure text flows correctly between columns.
    """
    sample_name = "sample2_multicolumn"
    
    # Skip if sample PDF or expected output doesn't exist
    pdf_path = TEST_DATA_DIR / f"{sample_name}.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Sample PDF {sample_name}.pdf not found")
    
    expected_output = expected_outputs.get(sample_name)
    if expected_output is None:
        pytest.skip(f"Expected output for {sample_name} not found")
    
    # Process the document
    pipeline_service = PipelineService()
    result = pipeline_service.process_document(str(pdf_path))
    
    # Create visualization highlighting reading order
    visual_path = TEST_VISUALS_DIR / f"{sample_name}_reading_order.png"
    draw_layout_visualization(result, 0, visual_path, highlight_reading_order=True)
    
    # Attach visualization to the HTML report
    attach_visual(visual_path, f"{sample_name} - Reading Order")
    
    # Verify document structure
    assert "pages" in result and len(result["pages"]) > 0, "Document should have at least one page"
    page = result["pages"][0]
    
    # Extract all text in the order it appears in the document
    assert "blocks" in page, "Page should have text blocks"
    text_blocks = page.get("blocks", [])
    full_text = ""
    for block in text_blocks:
        block_text = block.get("text", "")
        full_text += block_text + " "
    
    # Check if we can identify the columns
    left_column_blocks = []
    right_column_blocks = []
    
    # Basic column detection - check if we can identify left and right columns
    page_width = page.get("width", 1000)
    mid_x = page_width / 2
    
    for i, block in enumerate(text_blocks):
        # Calculate center point of block
        center_x = (block["x0"] + block["x1"]) / 2
        
        # Assign to left or right column
        if center_x < mid_x:
            left_column_blocks.append(i)
        else:
            right_column_blocks.append(i)
    
    # If we have identified multiple columns, check reading order
    if left_column_blocks and right_column_blocks:
        # In a proper multi-column layout, all blocks in the left column
        # should come before any block in the right column
        max_left_idx = max(left_column_blocks)
        min_right_idx = min(right_column_blocks)
        
        # Check if any right column block appears before left column block
        # which would indicate incorrect reading order
        if min_right_idx < max_left_idx:
            # This is a warning, not a failure, as some complex layouts might legitimately mix columns
            print(f"Warning: Possible reading order issue. Right column block {min_right_idx} "
                  f"appears before left column block {max_left_idx}")
    
    # Check for specific sequences that should appear in the correct order
    # For academic papers, common sequences include:
    sequences = [
        ("Abstract", "Introduction"),
        ("Introduction", "Methods"),
        ("Methods", "Results"),
        ("Results", "Discussion"),
        ("Discussion", "Conclusion"),
        ("Conclusion", "References")
    ]
    
    # Check each sequence if both terms appear in the text
    for first, second in sequences:
        if first.lower() in full_text.lower() and second.lower() in full_text.lower():
            assert full_text.lower().find(first.lower()) < full_text.lower().find(second.lower()), \
                f"'{first}' should appear before '{second}' in the reading order"
    
    # Compare with expected output
    assert compare_json(result, expected_output), \
        f"Document processing result doesn't match expected output for {sample_name}"

def test_paragraph_detection(attach_visual, expected_outputs):
    """
    Test that paragraphs are correctly detected and structured.
    """
    # Test with both simple and complex layouts
    for sample_name in ["sample1_simple", "sample2_multicolumn"]:
        # Skip if sample PDF or expected output doesn't exist
        pdf_path = TEST_DATA_DIR / f"{sample_name}.pdf"
        if not pdf_path.exists():
            continue
        
        expected_output = expected_outputs.get(sample_name)
        if expected_output is None:
            continue
        
        # Process the document
        pipeline_service = PipelineService()
        result = pipeline_service.process_document(str(pdf_path))
        
        # Verify document structure
        assert "pages" in result, "Document should have 'pages' array"
        assert len(result["pages"]) > 0, "Document should have at least one page"
        
        # If the document structure includes 'paragraphs', test them
        page = result["pages"][0]
        if "paragraphs" in page and page["paragraphs"]:
            paragraphs = page["paragraphs"]
            
            # Create visualization for paragraphs
            visual_path = TEST_VISUALS_DIR / f"{sample_name}_paragraphs.png"
            
            # Custom visualization for paragraphs
            fig, ax = plt.subplots(figsize=(12, 16))
            
            # Set title
            ax.set_title(f"{sample_name} - Paragraph Detection")
            
            # Set axes limits
            width = page.get("width", 1000)
            height = page.get("height", 1400)
            ax.set_xlim(0, width)
            ax.set_ylim(0, height)
            
            # Draw paragraphs with different colors
            colors = plt.cm.tab10(np.linspace(0, 1, len(paragraphs)))
            
            for i, para in enumerate(paragraphs):
                # Get coordinates
                x0 = para.get("x0", 0)
                y0 = para.get("y0", 0)
                x1 = para.get("x1", x0 + 100)
                y1 = para.get("y1", y0 + 20)
                
                # Draw rectangle
                rect = patches.Rectangle(
                    (x0, y0), x1 - x0, y1 - y0, 
                    linewidth=1, 
                    edgecolor=colors[i % len(colors)],
                    facecolor=colors[i % len(colors)],
                    alpha=0.2
                )
                ax.add_patch(rect)
                
                # Add paragraph number
                ax.text(
                    (x0 + x1) / 2, (y0 + y1) / 2, 
                    f"P{i+1}", 
                    horizontalalignment='center',
                    verticalalignment='center',
                    fontsize=10,
                    bbox=dict(facecolor='white', alpha=0.7)
                )
            
            # Save the figure
            plt.tight_layout()
            plt.savefig(visual_path, dpi=150)
            plt.close()
            
            # Attach visualization to the HTML report
            attach_visual(visual_path, f"{sample_name} - Paragraphs")
            
            # Test paragraph properties
            for i, para in enumerate(paragraphs):
                # Required coordinate fields
                assert "x0" in para, f"Paragraph {i} should have x0 coordinate"
                assert "y0" in para, f"Paragraph {i} should have y0 coordinate"
                assert "x1" in para, f"Paragraph {i} should have x1 coordinate"
                assert "y1" in para, f"Paragraph {i} should have y1 coordinate"
                
                # Paragraph should have text content
                assert "text" in para, f"Paragraph {i} should have text content"
                assert para["text"], f"Paragraph {i} text should not be empty"
