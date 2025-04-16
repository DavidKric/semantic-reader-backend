"""
Tests for OCR text extraction functionality.

This module validates that the document processing correctly extracts text from
various types of documents, especially scanned documents requiring OCR.
"""

import os
import pytest
import json
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from difflib import SequenceMatcher

# Import application modules
try:
    from app.services.pipeline_service import PipelineService
except ImportError:
    pytest.skip("PipelineService not available", allow_module_level=True)

# Import test utilities
from ..conftest import TEST_DATA_DIR, TEST_EXPECTED_DIR, TEST_VISUALS_DIR


def visualize_ocr_text(document, page_idx, output_path, highlight_confidence=True):
    """
    Create a visualization of OCR extracted text with confidence scores.
    
    Args:
        document: Processed document JSON
        page_idx: Index of the page to visualize
        output_path: Path to save the visualization image
        highlight_confidence: Whether to color-code blocks by confidence
        
    Returns:
        Path: Path to the saved visualization image
    """
    # Create figure and axes
    fig, ax = plt.subplots(figsize=(12, 16))
    
    # Set title
    ax.set_title(f"OCR Text Extraction - Page {page_idx + 1}")
    
    try:
        page = document.get("pages", [])[page_idx]
        width = page.get("width", 1000)
        height = page.get("height", 1400)
        
        # Set axes limits
        ax.set_xlim(0, width)
        ax.set_ylim(0, height)
        
        # Draw text blocks with confidence information
        blocks = page.get("blocks", [])
        
        # If no blocks, try using "words" or other text elements if available
        if not blocks and "words" in page:
            blocks = page.get("words", [])
        
        if not blocks:
            ax.text(
                width/2, height/2,
                "No text blocks found in document",
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=14,
                bbox=dict(facecolor='white', alpha=0.8)
            )
        else:
            # Generate colors based on confidence if available
            if highlight_confidence:
                # Create a color map function (red = low confidence, green = high confidence)
                def confidence_color(confidence):
                    if confidence is None:
                        return 'blue'  # Default color if no confidence score
                    # Red to green gradient based on confidence
                    r = max(0, min(1, 2 * (1 - confidence)))
                    g = max(0, min(1, 2 * confidence - 0.5))
                    return (r, g, 0)  # RGB tuple
            
            # Draw each text block/word
            for i, block in enumerate(blocks):
                # Get coordinates
                x0 = block.get("x0", 0)
                y0 = block.get("y0", 0)
                x1 = block.get("x1", x0 + 100)
                y1 = block.get("y1", y0 + 20)
                
                # Get confidence score if available
                confidence = block.get("confidence", None)
                
                # Determine color based on confidence
                if highlight_confidence and confidence is not None:
                    color = confidence_color(confidence)
                else:
                    color = 'blue'
                
                # Draw rectangle
                rect = patches.Rectangle(
                    (x0, y0), x1 - x0, y1 - y0,
                    linewidth=1,
                    edgecolor=color,
                    facecolor='none'
                )
                ax.add_patch(rect)
                
                # Add text content and confidence
                text = block.get("text", "")
                conf_text = f" ({confidence:.2f})" if confidence is not None else ""
                
                # Truncate text if too long
                if len(text) > 20:
                    display_text = text[:17] + "..."
                else:
                    display_text = text
                
                # Add text label to the rectangle
                ax.text(
                    x0, y0 - 5,
                    f"{display_text}{conf_text}",
                    fontsize=7,
                    color=color,
                    verticalalignment='bottom'
                )
            
            # Add confidence scale if we're highlighting confidence
            if highlight_confidence:
                # Create a color scale on the right side
                ax_scale = fig.add_axes([0.92, 0.3, 0.02, 0.4])
                cmap = plt.cm.RdYlGn  # Red-Yellow-Green colormap
                norm = plt.Normalize(0, 1)
                cb = plt.colorbar(
                    plt.cm.ScalarMappable(norm=norm, cmap=cmap),
                    cax=ax_scale,
                    orientation='vertical'
                )
                cb.set_label('Confidence Score')
                cb.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
                
    except (IndexError, KeyError) as e:
        # If document structure doesn't match expectations, draw empty diagram
        ax.text(
            width/2, height/2,
            f"Error visualizing OCR text: {str(e)}",
            horizontalalignment='center',
            verticalalignment='center'
        )
    
    # Save the figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    return output_path


def text_similarity(text1, text2):
    """
    Calculate the similarity between two text strings.
    
    Args:
        text1: First text string
        text2: Second text string
        
    Returns:
        float: Similarity ratio between 0 and 1
    """
    # Use SequenceMatcher to calculate similarity ratio
    return SequenceMatcher(None, text1, text2).ratio()


def test_ocr_text_structure(expected_outputs):
    """
    Test that OCR text elements have the expected structure with all required fields.
    
    Args:
        expected_outputs: Fixture providing expected outputs
    """
    # We'll use the scanned document sample for this test
    sample_name = "sample3_scanned"
    
    # Skip if expected output doesn't exist
    expected_output = expected_outputs.get(sample_name)
    if expected_output is None:
        pytest.skip(f"Expected output for {sample_name} not found")
    
    # Check document structure
    assert "pages" in expected_output, "Document should have 'pages' array"
    assert len(expected_output["pages"]) > 0, "Document should have at least one page"
    
    # Get the first page
    page = expected_output["pages"][0]
    
    # Verify text blocks exist
    assert "blocks" in page, "Page should have text blocks"
    assert len(page["blocks"]) > 0, "Page should have at least one text block"
    
    # Check text block structure
    for i, block in enumerate(page["blocks"]):
        # Required coordinate fields
        assert "x0" in block, f"Block {i} should have x0 coordinate"
        assert "y0" in block, f"Block {i} should have y0 coordinate"
        assert "x1" in block, f"Block {i} should have x1 coordinate"
        assert "y1" in block, f"Block {i} should have y1 coordinate"
        
        # Text content
        assert "text" in block, f"Block {i} should have text content"
        
        # OCR-specific fields
        if "confidence" in block:
            confidence = block["confidence"]
            assert 0 <= confidence <= 1, f"Block {i} confidence should be between 0 and 1"
            
        if "font" in block:
            assert isinstance(block["font"], str), f"Block {i} font should be a string"
            
        if "font_size" in block:
            assert isinstance(block["font_size"], (int, float)), f"Block {i} font size should be a number"


@pytest.mark.parametrize("sample_name", [
    "sample3_scanned",  # Scanned document requiring OCR
    "sample1_simple",   # Simple text for comparison
])
def test_ocr_text_extraction(sample_name, attach_visual, compare_json, expected_outputs):
    """
    Test that text is correctly extracted from documents, including those requiring OCR.
    
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
    
    # Create visualization for OCR text extraction
    visual_path = TEST_VISUALS_DIR / f"{sample_name}_ocr.png"
    visualize_ocr_text(result, 0, visual_path, highlight_confidence=True)
    
    # Attach visualization to the HTML report
    attach_visual(visual_path, f"{sample_name} - OCR Extraction")
    
    # Verify document structure
    assert "pages" in result, "Document should have 'pages' array"
    assert len(result["pages"]) > 0, "Document should have at least one page"
    
    # Verify text blocks exist
    first_page = result["pages"][0]
    assert "blocks" in first_page, "Page should have text blocks"
    assert len(first_page["blocks"]) > 0, "Page should have at least one text block"
    
    # Check if all blocks have text content
    for i, block in enumerate(first_page["blocks"]):
        assert "text" in block, f"Block {i} should have text content"
        if i < 5:  # Only check first few blocks to avoid too many assertions
            assert block["text"], f"Block {i} text should not be empty"
    
    # Verify text extraction by checking total text length
    total_text = ""
    for block in first_page["blocks"]:
        total_text += block.get("text", "") + " "
    
    # Text should have reasonable length (at least some characters)
    assert len(total_text) > 50, "Extracted text is too short"
    
    # Compare with expected output, allowing for minor differences
    assert compare_json(result, expected_output, ignore_keys=["confidence"]), \
        f"Document processing result doesn't match expected output for {sample_name}"


def test_ocr_confidence_scores(attach_visual, expected_outputs):
    """
    Test OCR confidence scores for text extraction from scanned documents.
    
    Args:
        attach_visual: Fixture to attach visualizations to the HTML report
        expected_outputs: Fixture providing expected outputs
    """
    # Use the scanned document for this test
    sample_name = "sample3_scanned"
    
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
    
    # Create visualization highlighting confidence scores
    visual_path = TEST_VISUALS_DIR / f"{sample_name}_confidence.png"
    visualize_ocr_text(result, 0, visual_path, highlight_confidence=True)
    
    # Attach visualization to the HTML report
    attach_visual(visual_path, f"{sample_name} - OCR Confidence")
    
    # Verify document structure and text blocks
    assert "pages" in result, "Document should have 'pages' array"
    assert len(result["pages"]) > 0, "Document should have at least one page"
    
    first_page = result["pages"][0]
    assert "blocks" in first_page, "Page should have text blocks"
    
    blocks = first_page["blocks"]
    if not blocks:
        pytest.skip("No text blocks found for confidence testing")
    
    # Check confidence scores for each block
    confidence_values = []
    for block in blocks:
        if "confidence" in block:
            confidence = block["confidence"]
            assert isinstance(confidence, (int, float)), "Confidence should be a number"
            assert 0 <= confidence <= 1, "Confidence should be between 0 and 1"
            confidence_values.append(confidence)
    
    # Skip if no confidence values were found
    if not confidence_values:
        pytest.skip("No confidence scores found in blocks")
    
    # Calculate average confidence - should be reasonably high for most documents
    avg_confidence = sum(confidence_values) / len(confidence_values)
    
    # Create a histogram visualization of confidence scores
    hist_path = TEST_VISUALS_DIR / f"{sample_name}_confidence_hist.png"
    plt.figure(figsize=(10, 6))
    plt.hist(confidence_values, bins=20, range=(0, 1), alpha=0.7)
    plt.xlabel('Confidence Score')
    plt.ylabel('Number of Text Blocks')
    plt.title(f'OCR Confidence Score Distribution (Avg: {avg_confidence:.2f})')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(hist_path, dpi=150)
    plt.close()
    
    # Attach histogram to HTML report
    attach_visual(hist_path, f"{sample_name} - Confidence Distribution")
    
    # Add basic assertions about confidence distribution
    # These thresholds might need adjustment based on actual OCR performance
    assert avg_confidence > 0.5, "Average OCR confidence is too low"


def test_ocr_text_positioning(attach_visual, expected_outputs):
    """
    Test that OCR text blocks are correctly positioned on the page.
    
    Args:
        attach_visual: Fixture to attach visualizations to the HTML report
        expected_outputs: Fixture providing expected outputs
    """
    # Use the scanned document for this test
    sample_name = "sample3_scanned"
    
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
    
    # Verify document structure
    assert "pages" in result, "Document should have 'pages' array"
    assert len(result["pages"]) > 0, "Document should have at least one page"
    
    # Get page dimensions
    first_page = result["pages"][0]
    width = first_page.get("width", 1000)
    height = first_page.get("height", 1400)
    
    # Check text block positioning
    blocks = first_page.get("blocks", [])
    if not blocks:
        pytest.skip("No text blocks found for position testing")
    
    # Create visualization for text positioning
    fig, ax = plt.subplots(figsize=(12, 16))
    ax.set_title(f"{sample_name} - OCR Text Positioning")
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    
    # Draw page outline
    page_rect = patches.Rectangle(
        (0, 0), width, height,
        linewidth=2, edgecolor='black', facecolor='none'
    )
    ax.add_patch(page_rect)
    
    # Track vertical positions to check for reading order
    y_positions = []
    
    # Draw each text block with position info
    for i, block in enumerate(blocks):
        x0 = block.get("x0", 0)
        y0 = block.get("y0", 0)
        x1 = block.get("x1", x0 + 100)
        y1 = block.get("y1", y0 + 20)
        
        # Store position information
        y_positions.append((i, (y0 + y1) / 2))
        
        # Check boundary containment
        assert 0 <= x0 <= width, f"Block {i} x0 outside page bounds"
        assert 0 <= y0 <= height, f"Block {i} y0 outside page bounds"
        assert 0 <= x1 <= width, f"Block {i} x1 outside page bounds"
        assert 0 <= y1 <= height, f"Block {i} y1 outside page bounds"
        
        # Check bounding box validity
        assert x1 > x0, f"Block {i} has invalid x-bounds"
        assert y1 > y0, f"Block {i} has invalid y-bounds"
        
        # Draw the block
        rect = patches.Rectangle(
            (x0, y0), x1 - x0, y1 - y0,
            linewidth=1, edgecolor='blue', facecolor='none'
        )
        ax.add_patch(rect)
        
        # Add block index
        ax.text(
            (x0 + x1) / 2, (y0 + y1) / 2,
            str(i),
            horizontalalignment='center',
            verticalalignment='center',
            fontsize=8,
            bbox=dict(facecolor='white', alpha=0.7)
        )
    
    # Save visualization
    position_path = TEST_VISUALS_DIR / f"{sample_name}_positioning.png"
    plt.tight_layout()
    plt.savefig(position_path, dpi=150)
    plt.close()
    
    # Attach to HTML report
    attach_visual(position_path, f"{sample_name} - Text Positioning")
    
    # Sort positions by y-coordinate to check for roughly top-to-bottom flow
    y_positions.sort(key=lambda x: x[1])
    
    # Create a visualization of reading order based on y-position
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title(f"{sample_name} - Text Y-Position vs. Block Index")
    block_indices = [pos[0] for pos in y_positions]
    y_coords = [pos[1] for pos in y_positions]
    
    ax.scatter(block_indices, y_coords, alpha=0.7)
    ax.set_xlabel('Block Index (Reading Order)')
    ax.set_ylabel('Y-Position on Page')
    ax.grid(True, alpha=0.3)
    
    # Add trend line to check for overall top-to-bottom flow
    z = np.polyfit(block_indices, y_coords, 1)
    p = np.poly1d(z)
    ax.plot(block_indices, p(block_indices), "r--", alpha=0.7)
    
    order_path = TEST_VISUALS_DIR / f"{sample_name}_reading_order_y.png"
    plt.tight_layout()
    plt.savefig(order_path, dpi=150)
    plt.close()
    
    # Attach to HTML report
    attach_visual(order_path, f"{sample_name} - Reading Order Y-Position")


def test_ocr_language_detection(expected_outputs):
    """
    Test language detection in the OCR text extraction process.
    
    Args:
        expected_outputs: Fixture providing expected outputs
    """
    # Test all document samples with expected outputs
    for sample_name, expected_output in expected_outputs.items():
        # Process the document if sample exists
        pdf_path = TEST_DATA_DIR / f"{sample_name}.pdf"
        if not pdf_path.exists():
            continue
        
        # Skip if no metadata or language info in expected output
        if "metadata" not in expected_output:
            continue
        
        # Check language metadata
        metadata = expected_output.get("metadata", {})
        if "language" not in metadata:
            continue
        
        # Process the document
        pipeline_service = PipelineService()
        result = pipeline_service.process_document(str(pdf_path))
        
        # Verify document structure
        assert "metadata" in result, "Document should have metadata"
        result_metadata = result.get("metadata", {})
        
        # Check language detection
        assert "language" in result_metadata, "Document metadata should include language"
        detected_language = result_metadata["language"]
        expected_language = metadata["language"]
        
        # Language should match expected language
        assert detected_language == expected_language, \
            f"Detected language '{detected_language}' doesn't match expected '{expected_language}'"
        
        # Check if RTL detection is available
        if "is_rtl_language" in metadata:
            expected_rtl = metadata["is_rtl_language"]
            if "is_rtl_language" in result_metadata:
                detected_rtl = result_metadata["is_rtl_language"]
                assert detected_rtl == expected_rtl, \
                    f"RTL detection doesn't match expected value for {sample_name}"


def test_ocr_text_content_accuracy(expected_outputs):
    """
    Test the accuracy of extracted text against expected content.
    
    Args:
        expected_outputs: Fixture providing expected outputs
    """
    # Use simple document for controlled text comparison
    sample_name = "sample1_simple"
    
    # Skip if expected output doesn't exist
    expected_output = expected_outputs.get(sample_name)
    if expected_output is None:
        pytest.skip(f"Expected output for {sample_name} not found")
    
    # Skip if sample PDF doesn't exist
    pdf_path = TEST_DATA_DIR / f"{sample_name}.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Sample PDF {sample_name}.pdf not found")
    
    # Process the document
    pipeline_service = PipelineService()
    result = pipeline_service.process_document(str(pdf_path))
    
    # Extract full text from result
    result_text = ""
    for page in result.get("pages", []):
        for block in page.get("blocks", []):
            result_text += block.get("text", "") + " "
    
    # Extract full text from expected output
    expected_text = ""
    for page in expected_output.get("pages", []):
        for block in page.get("blocks", []):
            expected_text += block.get("text", "") + " "
    
    # Clean up whitespace in both texts
    result_text = " ".join(result_text.split())
    expected_text = " ".join(expected_text.split())
    
    # Skip if either text is empty
    if not result_text or not expected_text:
        pytest.skip("Not enough text content for accuracy testing")
    
    # Calculate text similarity
    similarity = text_similarity(result_text, expected_text)
    
    # Text similarity should be high (threshold may need adjustment)
    assert similarity > 0.8, f"Text similarity ({similarity:.2f}) is too low"
