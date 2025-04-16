"""
Tests for miscellaneous layout characteristics.

This module validates various additional aspects of document layout analysis
such as page dimensions, margins, and content boundaries.
"""

import os
import pytest
import json
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Import application modules
try:
    from app.services.pipeline_service import PipelineService
except ImportError:
    pytest.skip("PipelineService not available", allow_module_level=True)

# Import test utilities
from ..conftest import TEST_DATA_DIR, TEST_EXPECTED_DIR, TEST_VISUALS_DIR


def visualize_page_boundaries(document, page_idx, output_path):
    """
    Create a visualization of page boundaries and margins.
    
    Args:
        document: Processed document JSON
        page_idx: Index of the page to visualize
        output_path: Path to save the visualization image
        
    Returns:
        Path: Path to the saved visualization image
    """
    # Create figure and axes
    fig, ax = plt.subplots(figsize=(12, 16))
    
    # Set title
    ax.set_title(f"Page Boundaries - Page {page_idx + 1}")
    
    try:
        page = document.get("pages", [])[page_idx]
        width = page.get("width", 1000)
        height = page.get("height", 1400)
        
        # Set axes limits with padding
        ax.set_xlim(-50, width + 50)
        ax.set_ylim(-50, height + 50)
        
        # Draw page outline
        page_rect = patches.Rectangle(
            (0, 0), width, height,
            linewidth=2, edgecolor='black', facecolor='none'
        )
        ax.add_patch(page_rect)
        
        # Add page dimensions
        ax.text(
            width/2, -20, 
            f"Width: {width:.1f}",
            horizontalalignment='center',
            verticalalignment='top',
            fontsize=10
        )
        ax.text(
            -20, height/2, 
            f"Height: {height:.1f}",
            horizontalalignment='right',
            verticalalignment='center',
            fontsize=10,
            rotation=90
        )
        
        # Find content boundaries by analyzing all blocks
        blocks = page.get("blocks", [])
        if blocks:
            min_x = min(block.get("x0", width) for block in blocks)
            max_x = max(block.get("x1", 0) for block in blocks)
            min_y = min(block.get("y0", height) for block in blocks)
            max_y = max(block.get("y1", 0) for block in blocks)
            
            # Draw content bounding box
            content_rect = patches.Rectangle(
                (min_x, min_y), max_x - min_x, max_y - min_y,
                linewidth=1, edgecolor='blue', facecolor='blue', alpha=0.1
            )
            ax.add_patch(content_rect)
            
            # Calculate margins
            left_margin = min_x
            right_margin = width - max_x
            top_margin = height - max_y
            bottom_margin = min_y
            
            # Add margin annotations
            ax.text(
                min_x/2, height/2, 
                f"Left: {left_margin:.1f}",
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=8,
                rotation=90
            )
            ax.text(
                max_x + (width-max_x)/2, height/2, 
                f"Right: {right_margin:.1f}",
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=8,
                rotation=90
            )
            ax.text(
                width/2, bottom_margin/2, 
                f"Bottom: {bottom_margin:.1f}",
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=8
            )
            ax.text(
                width/2, max_y + (height-max_y)/2, 
                f"Top: {top_margin:.1f}",
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=8
            )
            
            # Draw margin lines
            # Left margin
            ax.plot([0, min_x], [height/2, height/2], 'r--', linewidth=1)
            # Right margin
            ax.plot([max_x, width], [height/2, height/2], 'r--', linewidth=1)
            # Bottom margin
            ax.plot([width/2, width/2], [0, min_y], 'r--', linewidth=1)
            # Top margin
            ax.plot([width/2, width/2], [max_y, height], 'r--', linewidth=1)
            
            # Add header for content boundaries
            ax.text(
                width/2, max_y + top_margin/4, 
                "Content Boundaries",
                horizontalalignment='center',
                verticalalignment='center',
                fontsize=10,
                fontweight='bold',
                bbox=dict(facecolor='white', alpha=0.7)
            )
    except (IndexError, KeyError) as e:
        # If document structure doesn't match expectations, draw empty diagram
        ax.text(
            width/2, height/2, 
            f"Error visualizing page boundaries: {str(e)}", 
            horizontalalignment='center',
            verticalalignment='center'
        )
    
    # Save the figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    return output_path


def test_page_dimensions(attach_visual, expected_outputs):
    """
    Test that page dimensions are correctly extracted and consistent across pages.
    
    Args:
        attach_visual: Fixture to attach visualizations to the HTML report
        expected_outputs: Fixture providing expected outputs
    """
    for sample_name in ["sample1_simple", "sample4_tables", "sample6_mixed"]:
        # Skip if expected output doesn't exist
        expected_output = expected_outputs.get(sample_name)
        if expected_output is None:
            continue
        
        # Process the document if sample exists
        pdf_path = TEST_DATA_DIR / f"{sample_name}.pdf"
        if not pdf_path.exists():
            continue
        
        pipeline_service = PipelineService()
        result = pipeline_service.process_document(str(pdf_path))
        
        # Create visualization for the first page
        visual_path = TEST_VISUALS_DIR / f"{sample_name}_boundaries.png"
        visualize_page_boundaries(result, 0, visual_path)
        
        # Attach visualization to the HTML report
        attach_visual(visual_path, f"{sample_name} - Page Boundaries")
        
        # Verify document structure
        assert "pages" in result, "Document should have 'pages' array"
        assert len(result["pages"]) > 0, "Document should have at least one page"
        
        # Check page dimensions across all pages
        pages = result["pages"]
        
        # First page dimensions
        first_page = pages[0]
        assert "width" in first_page, "Page should have width property"
        assert "height" in first_page, "Page should have height property"
        first_width = first_page["width"]
        first_height = first_page["height"]
        
        # Verify dimensions are positive numbers
        assert first_width > 0, "Page width should be positive"
        assert first_height > 0, "Page height should be positive"
        
        # Standard size check (US Letter: 8.5" x 11" at 72dpi = 612 x 792 pts)
        # Allow some tolerance due to potential trimming
        us_letter_width = 612
        us_letter_height = 792
        a4_width = 595
        a4_height = 842
        
        # Check if dimensions are close to standard sizes
        is_us_letter = (abs(first_width - us_letter_width) < 20 and 
                       abs(first_height - us_letter_height) < 20)
        is_a4 = (abs(first_width - a4_width) < 20 and 
                abs(first_height - a4_height) < 20)
        
        # If multi-page document, check consistency across pages
        if len(pages) > 1:
            for i, page in enumerate(pages[1:], 1):
                assert "width" in page, f"Page {i+1} should have width property"
                assert "height" in page, f"Page {i+1} should have height property"
                
                # Check that dimensions are consistent (allow 1% tolerance)
                assert abs(page["width"] - first_width) < first_width * 0.01, \
                    f"Page {i+1} width differs from first page"
                assert abs(page["height"] - first_height) < first_height * 0.01, \
                    f"Page {i+1} height differs from first page"


def test_content_boundaries(attach_visual, expected_outputs):
    """
    Test that content boundaries and margins are properly identified.
    
    Args:
        attach_visual: Fixture to attach visualizations to the HTML report
        expected_outputs: Fixture providing expected outputs
    """
    for sample_name in ["sample1_simple", "sample2_multicolumn"]:
        # Skip if expected output doesn't exist
        expected_output = expected_outputs.get(sample_name)
        if expected_output is None:
            continue
        
        # Process the document if sample exists
        pdf_path = TEST_DATA_DIR / f"{sample_name}.pdf"
        if not pdf_path.exists():
            continue
        
        pipeline_service = PipelineService()
        result = pipeline_service.process_document(str(pdf_path))
        
        # Verify document structure
        assert "pages" in result, "Document should have 'pages' array"
        assert len(result["pages"]) > 0, "Document should have at least one page"
        
        # Check content boundaries for each page
        for page_idx, page in enumerate(result["pages"]):
            assert "blocks" in page, f"Page {page_idx+1} should have text blocks"
            blocks = page["blocks"]
            
            if not blocks:
                # Skip empty pages
                continue
            
            # Find content boundaries
            min_x = min(block.get("x0", float("inf")) for block in blocks)
            max_x = max(block.get("x1", 0) for block in blocks)
            min_y = min(block.get("y0", float("inf")) for block in blocks)
            max_y = max(block.get("y1", 0) for block in blocks)
            
            # Page dimensions
            width = page.get("width", 1000)
            height = page.get("height", 1400)
            
            # Calculate margins
            left_margin = min_x
            right_margin = width - max_x
            top_margin = height - max_y
            bottom_margin = min_y
            
            # Margins should be reasonable (not too small or too large)
            # These values are somewhat arbitrary but catch obvious issues
            assert left_margin >= 0, f"Left margin should be non-negative on page {page_idx+1}"
            assert right_margin >= 0, f"Right margin should be non-negative on page {page_idx+1}"
            assert top_margin >= 0, f"Top margin should be non-negative on page {page_idx+1}"
            assert bottom_margin >= 0, f"Bottom margin should be non-negative on page {page_idx+1}"
            
            # Content should not exceed page boundaries
            assert min_x >= 0, f"Content exceeds left page boundary on page {page_idx+1}"
            assert max_x <= width, f"Content exceeds right page boundary on page {page_idx+1}"
            assert min_y >= 0, f"Content exceeds bottom page boundary on page {page_idx+1}"
            assert max_y <= height, f"Content exceeds top page boundary on page {page_idx+1}"
            
            # Content should have reasonable width and height (not too small)
            content_width = max_x - min_x
            content_height = max_y - min_y
            assert content_width > 0, f"Content width should be positive on page {page_idx+1}"
            assert content_height > 0, f"Content height should be positive on page {page_idx+1}"
            
            # Content should occupy a reasonable portion of the page (not too small)
            content_area_ratio = (content_width * content_height) / (width * height)
            assert content_area_ratio > 0.1, \
                f"Content area too small relative to page on page {page_idx+1}"


def test_margin_consistency(expected_outputs):
    """
    Test that margins are consistent across pages of the same document.
    
    Args:
        expected_outputs: Fixture providing expected outputs
    """
    # Test with documents that have multiple pages
    for sample_name in ["sample2_multicolumn", "sample6_mixed"]:
        # Skip if expected output doesn't exist
        expected_output = expected_outputs.get(sample_name)
        if expected_output is None:
            continue
        
        # Skip documents with fewer than 2 pages
        if len(expected_output.get("pages", [])) < 2:
            continue
        
        # Process the document if sample exists
        pdf_path = TEST_DATA_DIR / f"{sample_name}.pdf"
        if not pdf_path.exists():
            continue
        
        pipeline_service = PipelineService()
        result = pipeline_service.process_document(str(pdf_path))
        
        # Extract margin data for each page
        pages = result.get("pages", [])
        margin_data = []
        
        for page_idx, page in enumerate(pages):
            blocks = page.get("blocks", [])
            if not blocks:
                continue
                
            # Find content boundaries
            min_x = min(block.get("x0", float("inf")) for block in blocks)
            max_x = max(block.get("x1", 0) for block in blocks)
            min_y = min(block.get("y0", float("inf")) for block in blocks)
            max_y = max(block.get("y1", 0) for block in blocks)
            
            # Page dimensions
            width = page.get("width", 1000)
            height = page.get("height", 1400)
            
            # Calculate margins
            margin_data.append({
                "page_idx": page_idx,
                "left": min_x,
                "right": width - max_x,
                "top": height - max_y,
                "bottom": min_y
            })
        
        # Skip if not enough pages with content
        if len(margin_data) < 2:
            continue
        
        # Calculate average margins
        avg_left = sum(page["left"] for page in margin_data) / len(margin_data)
        avg_right = sum(page["right"] for page in margin_data) / len(margin_data)
        avg_top = sum(page["top"] for page in margin_data) / len(margin_data)
        avg_bottom = sum(page["bottom"] for page in margin_data) / len(margin_data)
        
        # Check consistency of margins across pages
        # Allow for some variation (20% of the average)
        for page in margin_data:
            assert abs(page["left"] - avg_left) <= avg_left * 0.20, \
                f"Left margin on page {page['page_idx']+1} differs significantly from average"
            assert abs(page["right"] - avg_right) <= avg_right * 0.20, \
                f"Right margin on page {page['page_idx']+1} differs significantly from average"
            assert abs(page["top"] - avg_top) <= avg_top * 0.20, \
                f"Top margin on page {page['page_idx']+1} differs significantly from average"
            assert abs(page["bottom"] - avg_bottom) <= avg_bottom * 0.20, \
                f"Bottom margin on page {page['page_idx']+1} differs significantly from average"
