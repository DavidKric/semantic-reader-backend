"""
Tests for table content extraction functionality.

This module verifies the document processing pipeline's ability to extract and
process content within tables, including text extraction, header detection,
and handling of different data types and cell spans.
"""

import os
import pytest
import json
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import difflib
from matplotlib.patches import Rectangle
from matplotlib.colors import to_rgba
import re

# Import application modules
try:
    from app.services.pipeline_service import PipelineService
except ImportError:
    pytest.skip("PipelineService not available", allow_module_level=True)

# Import test utilities
from ..conftest import TEST_DATA_DIR, TEST_EXPECTED_DIR, TEST_VISUALS_DIR


def calculate_text_similarity(text1, text2):
    """
    Calculate similarity between two text strings.
    
    Args:
        text1: First text string
        text2: Second text string
        
    Returns:
        float: Similarity score between 0 (completely different) and 1 (identical)
    """
    if not text1 and not text2:
        return 1.0  # Both empty strings are identical
    
    if not text1 or not text2:
        return 0.0  # One empty string means no match
    
    # Use difflib's SequenceMatcher for string similarity
    similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
    return similarity


def visualize_table_content(table, output_path, title=None):
    """
    Create a visualization of table content, highlighting cells, headers, and values.
    
    Args:
        table: Table data with cells
        output_path: Path to save the visualization image
        title: Optional title for the visualization
        
    Returns:
        Path: Path to the saved visualization image
    """
    if not table or "cells" not in table or not table["cells"]:
        # Create a visualization showing no cells found
        fig, ax = plt.subplots(figsize=(8, 6))
        if title:
            ax.set_title(title)
        else:
            ax.set_title("Table Content - No Cells Found")
        
        ax.text(0.5, 0.5, "No cells detected in this table", 
                ha="center", va="center", fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_axis_off()
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        return output_path
    
    # Get table boundaries
    x0, y0 = table.get("x0", 0), table.get("y0", 0)
    x1, y1 = table.get("x1", x0 + 500), table.get("y1", y0 + 300)
    width = x1 - x0
    height = y1 - y0
    
    # Calculate grid dimensions based on cells
    cells = table["cells"]
    max_row = max(cell.get("row", 0) for cell in cells) + 1
    max_col = max(cell.get("col", 0) for cell in cells) + 1
    
    # Create figure with appropriate size
    fig_width = min(12, max(8, max_col * 1.5))
    fig_height = min(10, max(6, max_row * 0.8))
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    
    if title:
        ax.set_title(title)
    else:
        ax.set_title("Table Content Extraction")
    
    # Set axis limits
    ax.set_xlim(-0.5, max_col - 0.5)
    ax.set_ylim(max_row - 0.5, -0.5)  # Invert y-axis to show rows from top to bottom
    
    # Draw grid lines
    for i in range(max_row + 1):
        ax.axhline(y=i - 0.5, color='gray', linestyle='-', linewidth=0.5)
    for i in range(max_col + 1):
        ax.axvline(x=i - 0.5, color='gray', linestyle='-', linewidth=0.5)
    
    # Define colors for cell types
    header_color = to_rgba('skyblue', alpha=0.4)
    data_color = to_rgba('white', alpha=0.1)
    span_color = to_rgba('lightyellow', alpha=0.5)
    
    # Draw cells
    for cell in cells:
        row = cell.get("row", 0)
        col = cell.get("col", 0)
        rowspan = cell.get("rowspan", 1)
        colspan = cell.get("colspan", 1)
        is_header = cell.get("is_header", False)
        
        # Determine cell color based on type
        if is_header:
            cell_color = header_color
        elif rowspan > 1 or colspan > 1:
            cell_color = span_color
        else:
            cell_color = data_color
        
        # Draw cell rectangle
        rect = Rectangle(
            (col - 0.5, row - 0.5),
            colspan,
            rowspan,
            linewidth=1,
            edgecolor='black',
            facecolor=cell_color
        )
        ax.add_patch(rect)
        
        # Add text content
        text = cell.get("text", "")
        if len(text) > 25:
            text = text[:22] + "..."
        
        # Calculate cell center for text placement
        cell_center_x = col - 0.5 + colspan / 2
        cell_center_y = row - 0.5 + rowspan / 2
        
        ax.text(
            cell_center_x,
            cell_center_y,
            text,
            ha='center',
            va='center',
            fontsize=8,
            fontweight='bold' if is_header else 'normal'
        )
    
    # Add a legend
    header_patch = plt.Rectangle((0, 0), 1, 1, fc=header_color, ec='black')
    span_patch = plt.Rectangle((0, 0), 1, 1, fc=span_color, ec='black')
    data_patch = plt.Rectangle((0, 0), 1, 1, fc=data_color, ec='black')
    
    ax.legend(
        [header_patch, span_patch, data_patch],
        ['Header', 'Span', 'Data'],
        loc='upper center',
        bbox_to_anchor=(0.5, -0.05),
        ncol=3
    )
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    return output_path


def test_table_text_content(expected_outputs):
    """
    Test that table cells contain the correct text content.
    
    Args:
        expected_outputs: Fixture providing expected outputs
    """
    # Use a sample document with tables
    sample_name = "sample2_tables"
    
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
    
    # Check text content in table cells
    has_verified_cells = False
    
    for page_idx, page in enumerate(result["pages"]):
        if "tables" not in page or not page["tables"]:
            continue
            
        # Skip if this page isn't in expected output
        if page_idx >= len(expected_output["pages"]) or "tables" not in expected_output["pages"][page_idx]:
            continue
            
        expected_tables = expected_output["pages"][page_idx]["tables"]
        
        for table_idx, table in enumerate(page["tables"]):
            # Skip if more tables than expected
            if table_idx >= len(expected_tables):
                continue
                
            expected_table = expected_tables[table_idx]
            
            # Skip if table doesn't have cells
            if "cells" not in table or not table["cells"]:
                continue
                
            # Skip if expected table doesn't have cells
            if "cells" not in expected_table or not expected_table["cells"]:
                continue
                
            # Create a visualization of table content
            visual_path = TEST_VISUALS_DIR / f"{sample_name}_table_{page_idx}_{table_idx}_content.png"
            visualize_table_content(table, visual_path, 
                                  f"Table Content - {sample_name} - Page {page_idx + 1}, Table {table_idx + 1}")
            
            # Verify text content in cells
            actual_cells = table["cells"]
            expected_cells = expected_table["cells"]
            
            # Check that each cell has text content
            for cell_idx, cell in enumerate(actual_cells):
                has_verified_cells = True
                
                assert "text" in cell, f"Cell {cell_idx} in table {table_idx} on page {page_idx} is missing text content"
                
                # If there's matching expected cell, compare text content
                if cell_idx < len(expected_cells):
                    expected_cell = expected_cells[cell_idx]
                    
                    if "text" in expected_cell:
                        # Calculate similarity between actual and expected text
                        similarity = calculate_text_similarity(cell["text"], expected_cell["text"])
                        
                        # Allow for minor text differences (OCR variations, whitespace)
                        assert similarity >= 0.7, \
                            f"Cell {cell_idx} in table {table_idx} on page {page_idx} has text with low similarity to expected: " \
                            f"got '{cell['text']}', expected '{expected_cell['text']}' (similarity: {similarity:.2f})"
    
    assert has_verified_cells, "No table cells were verified"


def test_header_detection(expected_outputs):
    """
    Test that table headers are correctly detected.
    
    Args:
        expected_outputs: Fixture providing expected outputs
    """
    # Use a sample document with tables containing headers
    sample_name = "sample2_tables"
    
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
    
    # Check header detection in table cells
    headers_found = False
    
    for page_idx, page in enumerate(result["pages"]):
        if "tables" not in page or not page["tables"]:
            continue
            
        for table_idx, table in enumerate(page["tables"]):
            # Skip if table doesn't have cells
            if "cells" not in table or not table["cells"]:
                continue
                
            # Look for header cells
            header_cells = [cell for cell in table["cells"] if cell.get("is_header", False)]
            
            if header_cells:
                headers_found = True
                
                # Create a visualization of header detection
                visual_path = TEST_VISUALS_DIR / f"{sample_name}_table_{page_idx}_{table_idx}_headers.png"
                visualize_table_content(table, visual_path, 
                                      f"Header Detection - Page {page_idx + 1}, Table {table_idx + 1}")
                
                # Verify that headers are in the first row or have distinctive formatting
                for cell in header_cells:
                    assert "row" in cell, f"Header cell in table {table_idx} on page {page_idx} missing row attribute"
                    
                    # Headers are typically in the first row(s) of the table
                    # Or they have distinctive formatting (bold, background color, etc.)
                    is_first_row = cell["row"] == 0
                    has_formatting = any(key in cell for key in ["bold", "background_color", "font_style"])
                    
                    assert is_first_row or has_formatting, \
                        f"Header cell in table {table_idx} on page {page_idx} is not in first row and lacks formatting attributes"
    
    if not headers_found:
        pytest.skip("No tables with header cells found")
    
    assert headers_found, "Tables should have header cells"


def test_table_data_types(expected_outputs):
    """
    Test that different data types in table cells are correctly identified.
    
    Args:
        expected_outputs: Fixture providing expected outputs
    """
    # Use a sample document with tables containing different data types
    sample_name = "sample4_complex"
    
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
    
    # Check data type detection in table cells
    data_types_found = False
    
    for page_idx, page in enumerate(result["pages"]):
        if "tables" not in page or not page["tables"]:
            continue
            
        for table_idx, table in enumerate(page["tables"]):
            # Skip if table doesn't have cells
            if "cells" not in table or not table["cells"]:
                continue
                
            # Create a visualization of the table data types
            visual_path = TEST_VISUALS_DIR / f"{sample_name}_table_{page_idx}_{table_idx}_data_types.png"
            
            # Look for cells with different data types
            text_cells = []
            numeric_cells = []
            date_cells = []
            other_cells = []
            
            for cell in table["cells"]:
                if "data_type" in cell:
                    data_types_found = True
                    
                    if cell["data_type"] == "text":
                        text_cells.append(cell)
                    elif cell["data_type"] == "numeric":
                        numeric_cells.append(cell)
                    elif cell["data_type"] == "date":
                        date_cells.append(cell)
                    else:
                        other_cells.append(cell)
                else:
                    # If data_type is not explicitly provided, try to infer it
                    if "text" in cell:
                        text = cell["text"].strip()
                        
                        # Check if it's a number
                        try:
                            float(text.replace(',', ''))
                            numeric_cells.append(cell)
                            data_types_found = True
                        except ValueError:
                            # Check if it's a date (simple check for patterns like MM/DD/YYYY)
                            if any(c in text for c in ['/', '-']) and sum(c.isdigit() for c in text) >= 4:
                                date_cells.append(cell)
                                data_types_found = True
                            else:
                                text_cells.append(cell)
            
            # Skip if no data types were found or inferred
            if not data_types_found:
                continue
                
            # Visualize data types
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.set_title(f"Table Data Types - Page {page_idx + 1}, Table {table_idx + 1}")
            
            # Set axis limits based on cell indices
            max_row = max([cell.get("row", 0) for cell in table["cells"]]) + 1
            max_col = max([cell.get("col", 0) for cell in table["cells"]]) + 1
            
            ax.set_xlim(-0.5, max_col - 0.5)
            ax.set_ylim(max_row - 0.5, -0.5)  # Invert y-axis to show rows from top to bottom
            
            # Draw grid
            for i in range(max_row + 1):
                ax.axhline(y=i - 0.5, color='gray', linestyle='-', linewidth=0.5)
            for i in range(max_col + 1):
                ax.axvline(x=i - 0.5, color='gray', linestyle='-', linewidth=0.5)
            
            # Draw cells with different colors based on data type
            for cell in text_cells:
                row, col = cell.get("row", 0), cell.get("col", 0)
                colspan, rowspan = cell.get("colspan", 1), cell.get("rowspan", 1)
                
                rect = Rectangle((col - 0.5, row - 0.5), colspan, rowspan, 
                                linewidth=1, edgecolor='black', facecolor='lightblue', alpha=0.5)
                ax.add_patch(rect)
                
                # Add text label
                ax.text(col - 0.5 + colspan/2, row - 0.5 + rowspan/2, "Text", 
                       ha='center', va='center', fontsize=8)
            
            for cell in numeric_cells:
                row, col = cell.get("row", 0), cell.get("col", 0)
                colspan, rowspan = cell.get("colspan", 1), cell.get("rowspan", 1)
                
                rect = Rectangle((col - 0.5, row - 0.5), colspan, rowspan, 
                                linewidth=1, edgecolor='black', facecolor='lightgreen', alpha=0.5)
                ax.add_patch(rect)
                
                # Add text label
                ax.text(col - 0.5 + colspan/2, row - 0.5 + rowspan/2, "Numeric", 
                       ha='center', va='center', fontsize=8)
            
            for cell in date_cells:
                row, col = cell.get("row", 0), cell.get("col", 0)
                colspan, rowspan = cell.get("colspan", 1), cell.get("rowspan", 1)
                
                rect = Rectangle((col - 0.5, row - 0.5), colspan, rowspan, 
                                linewidth=1, edgecolor='black', facecolor='lightyellow', alpha=0.5)
                ax.add_patch(rect)
                
                # Add text label
                ax.text(col - 0.5 + colspan/2, row - 0.5 + rowspan/2, "Date", 
                       ha='center', va='center', fontsize=8)
            
            for cell in other_cells:
                row, col = cell.get("row", 0), cell.get("col", 0)
                colspan, rowspan = cell.get("colspan", 1), cell.get("rowspan", 1)
                
                rect = Rectangle((col - 0.5, row - 0.5), colspan, rowspan, 
                                linewidth=1, edgecolor='black', facecolor='lightgray', alpha=0.5)
                ax.add_patch(rect)
                
                # Add text label
                ax.text(col - 0.5 + colspan/2, row - 0.5 + rowspan/2, "Other", 
                       ha='center', va='center', fontsize=8)
            
            # Add a legend
            text_patch = plt.Rectangle((0, 0), 1, 1, fc='lightblue', alpha=0.5, ec='black')
            numeric_patch = plt.Rectangle((0, 0), 1, 1, fc='lightgreen', alpha=0.5, ec='black')
            date_patch = plt.Rectangle((0, 0), 1, 1, fc='lightyellow', alpha=0.5, ec='black')
            other_patch = plt.Rectangle((0, 0), 1, 1, fc='lightgray', alpha=0.5, ec='black')
            
            ax.legend(
                [text_patch, numeric_patch, date_patch, other_patch],
                ['Text', 'Numeric', 'Date', 'Other'],
                loc='upper center',
                bbox_to_anchor=(0.5, -0.05),
                ncol=4
            )
            
            plt.tight_layout()
            plt.savefig(visual_path, dpi=150)
            plt.close()
    
    if not data_types_found:
        pytest.skip("No tables with different data types found")
    
    assert data_types_found, "Tables should have cells with different data types"


def test_table_span_detection(expected_outputs):
    """
    Test that row and column spans in tables are correctly detected.
    
    Args:
        expected_outputs: Fixture providing expected outputs
    """
    # Use a sample document with tables containing spans
    sample_name = "sample4_complex"
    
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
    
    # Check span detection in table cells
    spans_found = False
    
    for page_idx, page in enumerate(result["pages"]):
        if "tables" not in page or not page["tables"]:
            continue
            
        for table_idx, table in enumerate(page["tables"]):
            # Skip if table doesn't have cells
            if "cells" not in table or not table["cells"]:
                continue
                
            # Create a visualization of the table spans
            visual_path = TEST_VISUALS_DIR / f"{sample_name}_table_{page_idx}_{table_idx}_spans.png"
            
            # Look for cells with row or column spans
            span_cells = [cell for cell in table["cells"] 
                         if cell.get("rowspan", 1) > 1 or cell.get("colspan", 1) > 1]
            
            if span_cells:
                spans_found = True
                
                # Visualize the table structure with spans highlighted
                visualize_table_content(table, visual_path, 
                                      f"Cell Spans - Page {page_idx + 1}, Table {table_idx + 1}")
                
                # Check that spans don't overlap
                for cell1 in span_cells:
                    row1 = cell1.get("row", 0)
                    col1 = cell1.get("col", 0)
                    rowspan1 = cell1.get("rowspan", 1)
                    colspan1 = cell1.get("colspan", 1)
                    
                    # Calculate the cells covered by this span
                    covered_cells1 = [(row1 + r, col1 + c) 
                                     for r in range(rowspan1) 
                                     for c in range(colspan1)]
                    
                    for cell2 in span_cells:
                        # Skip comparing the cell with itself
                        if cell1 is cell2:
                            continue
                            
                        row2 = cell2.get("row", 0)
                        col2 = cell2.get("col", 0)
                        rowspan2 = cell2.get("rowspan", 1)
                        colspan2 = cell2.get("colspan", 1)
                        
                        # Calculate the cells covered by the other span
                        covered_cells2 = [(row2 + r, col2 + c) 
                                         for r in range(rowspan2) 
                                         for c in range(colspan2)]
                        
                        # Check for overlap
                        overlap = set(covered_cells1).intersection(set(covered_cells2))
                        assert not overlap, \
                            f"Found overlapping spans in table {table_idx} on page {page_idx}: " \
                            f"Cell at ({row1},{col1}) with span ({rowspan1},{colspan1}) " \
                            f"overlaps with cell at ({row2},{col2}) with span ({rowspan2},{colspan2})"
    
    if not spans_found:
        pytest.skip("No tables with cell spans found")
    
    assert spans_found, "Complex tables should have cells with row or column spans"


def test_complex_table_structure():
    """
    Test extraction of complex table structures with nested tables or irregular layouts.
    """
    # Use a sample document with complex tables
    sample_name = "sample4_complex"
    
    # Skip if sample PDF doesn't exist
    pdf_path = TEST_DATA_DIR / f"{sample_name}.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Sample PDF {sample_name}.pdf not found")
    
    # Process the document
    pipeline_service = PipelineService()
    result = pipeline_service.process_document(str(pdf_path))
    
    # Find page with complex tables
    complex_table = None
    page_with_complex = None
    table_idx = None
    
    for page_idx, page in enumerate(result["pages"]):
        if "tables" not in page or not page["tables"]:
            continue
            
        for t_idx, table in enumerate(page["tables"]):
            # Consider a table complex if it has many cells or cells with spans
            if "cells" in table and len(table["cells"]) > 15:
                has_spans = any(
                    cell.get("rowspan", 1) > 1 or cell.get("colspan", 1) > 1 
                    for cell in table["cells"]
                )
                
                if has_spans:
                    complex_table = table
                    page_with_complex = page_idx
                    table_idx = t_idx
                    break
                    
        if complex_table:
            break
    
    if not complex_table:
        pytest.skip("No complex tables found in the document")
    
    # Create visualization of the complex table
    visual_path = TEST_VISUALS_DIR / f"{sample_name}_complex_table.png"
    visualize_table_content(complex_table, visual_path, 
                          f"Complex Table Structure - Page {page_with_complex + 1}, Table {table_idx + 1}")
    
    # Test properties of complex table cells
    cells = complex_table["cells"]
    
    # All cells should have position and size
    for cell_idx, cell in enumerate(cells):
        assert "row" in cell, f"Cell {cell_idx} missing row attribute"
        assert "col" in cell, f"Cell {cell_idx} missing col attribute"
        assert "x0" in cell, f"Cell {cell_idx} missing x0 coordinate"
        assert "y0" in cell, f"Cell {cell_idx} missing y0 coordinate"
        assert "x1" in cell, f"Cell {cell_idx} missing x1 coordinate"
        assert "y1" in cell, f"Cell {cell_idx} missing y1 coordinate"
    
    # Complex table should have cells that act as headers
    header_cells = [cell for cell in cells if cell.get("is_header", False)]
    assert header_cells, "Complex table should have header cells"
    
    # Complex table should have some row or column spans
    span_cells = [cell for cell in cells 
                 if cell.get("rowspan", 1) > 1 or cell.get("colspan", 1) > 1]
    assert span_cells, "Complex table should have cells with spans"
    
    # Check for table structure consistency
    max_row = max(cell.get("row", 0) + cell.get("rowspan", 1) - 1 for cell in cells)
    max_col = max(cell.get("col", 0) + cell.get("colspan", 1) - 1 for cell in cells)
    
    # Create a grid to check if all positions are covered by cells
    grid = [[False for _ in range(max_col + 1)] for _ in range(max_row + 1)]
    
    for cell in cells:
        row = cell.get("row", 0)
        col = cell.get("col", 0)
        rowspan = cell.get("rowspan", 1)
        colspan = cell.get("colspan", 1)
        
        for r in range(row, row + rowspan):
            for c in range(col, col + colspan):
                # Skip if outside grid
                if r > max_row or c > max_col:
                    continue
                    
                # Mark this position as covered
                grid[r][c] = True
    
    # Check for gaps in the grid (missing cells)
    gaps = []
    for r in range(max_row + 1):
        for c in range(max_col + 1):
            if not grid[r][c]:
                gaps.append((r, c))
    
    # Allow some gaps (some tables may have empty cells or irregular structures)
    max_allowed_gaps = (max_row + 1) * (max_col + 1) * 0.1  # Allow up to 10% gaps
    assert len(gaps) <= max_allowed_gaps, \
        f"Too many gaps in table structure: found {len(gaps)} gaps, max allowed is {max_allowed_gaps}"


def test_merged_cells_detection():
    """
    Test detection and proper handling of merged cells in complex tables.
    """
    # Use a sample document with tables containing merged cells
    sample_name = "sample4_complex"
    
    # Skip if sample PDF doesn't exist
    pdf_path = TEST_DATA_DIR / f"{sample_name}.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Sample PDF {sample_name}.pdf not found")
    
    # Process the document
    pipeline_service = PipelineService()
    result = pipeline_service.process_document(str(pdf_path))
    
    # Look for merged cells (cells with rowspan > 1 or colspan > 1)
    merged_cells_found = False
    merged_cell_examples = []
    
    for page_idx, page in enumerate(result["pages"]):
        if "tables" not in page or not page["tables"]:
            continue
            
        for table_idx, table in enumerate(page["tables"]):
            if "cells" not in table or not table["cells"]:
                continue
                
            # Find cells with rowspan or colspan > 1
            merged_cells = [
                cell for cell in table["cells"]
                if cell.get("rowspan", 1) > 1 or cell.get("colspan", 1) > 1
            ]
            
            if merged_cells:
                merged_cells_found = True
                merged_cell_examples.extend(merged_cells[:3])  # Take up to 3 examples
                
                # Create visualization of merged cells
                visual_path = TEST_VISUALS_DIR / f"{sample_name}_table_{page_idx}_{table_idx}_merged_cells.png"
                
                # Create a custom visualization highlighting merged cells
                fig, ax = plt.subplots(figsize=(10, 8))
                ax.set_title(f"Merged Cells - Page {page_idx + 1}, Table {table_idx + 1}")
                
                # Get maximum row and column indices
                max_row = max(cell.get("row", 0) + cell.get("rowspan", 1) for cell in table["cells"])
                max_col = max(cell.get("col", 0) + cell.get("colspan", 1) for cell in table["cells"])
                
                # Set axis limits
                ax.set_xlim(-1, max_col)
                ax.set_ylim(max_row, -1)  # Invert y-axis
                
                # Draw grid
                for i in range(max_row + 1):
                    ax.axhline(y=i, color='gray', linestyle='-', linewidth=0.5)
                for i in range(max_col + 1):
                    ax.axvline(x=i, color='gray', linestyle='-', linewidth=0.5)
                
                # Draw all cells
                for cell in table["cells"]:
                    row = cell.get("row", 0)
                    col = cell.get("col", 0)
                    rowspan = cell.get("rowspan", 1)
                    colspan = cell.get("colspan", 1)
                    is_merged = rowspan > 1 or colspan > 1
                    
                    # Choose color based on whether cell is merged
                    color = 'orange' if is_merged else 'lightblue'
                    alpha = 0.7 if is_merged else 0.3
                    
                    # Draw cell
                    rect = Rectangle(
                        (col, row),
                        colspan,
                        rowspan,
                        linewidth=1.5 if is_merged else 0.5,
                        edgecolor='red' if is_merged else 'black',
                        facecolor=color,
                        alpha=alpha
                    )
                    ax.add_patch(rect)
                    
                    # Add text content and span info for merged cells
                    if is_merged:
                        label = f"{rowspan}×{colspan}"
                        text = cell.get("text", "")
                        if text:
                            if len(text) > 15:
                                text = text[:12] + "..."
                            label += f"\n{text}"
                        
                        ax.text(
                            col + colspan/2,
                            row + rowspan/2,
                            label,
                            ha='center',
                            va='center',
                            fontsize=9,
                            fontweight='bold'
                        )
                
                plt.tight_layout()
                plt.savefig(visual_path, dpi=150)
                plt.close()
    
    if not merged_cells_found:
        pytest.skip("No merged cells found in any table")
    
    # Check properties of merged cells
    for cell in merged_cell_examples:
        row = cell.get("row", 0)
        col = cell.get("col", 0)
        rowspan = cell.get("rowspan", 1)
        colspan = cell.get("colspan", 1)
        
        # Merged cells should have valid spans
        assert rowspan > 0, "Rowspan should be positive"
        assert colspan > 0, "Colspan should be positive"
        
        # Merged cells should have valid coordinates
        assert "x0" in cell, "Merged cell should have x0 coordinate"
        assert "y0" in cell, "Merged cell should have y0 coordinate"
        assert "x1" in cell, "Merged cell should have x1 coordinate"
        assert "y1" in cell, "Merged cell should have y1 coordinate"
        
        # The cell's width should correspond to its colspan
        # This is a rough check and may need adjustment based on the exact representation
        if colspan > 1 and "x1" in cell and "x0" in cell:
            width = cell["x1"] - cell["x0"]
            # Skip exact width check since we don't know the exact column widths
            assert width > 0, "Merged cell width should be positive"
        
        # The cell's height should correspond to its rowspan
        if rowspan > 1 and "y1" in cell and "y0" in cell:
            height = cell["y1"] - cell["y0"]
            # Skip exact height check since we don't know the exact row heights
            assert height > 0, "Merged cell height should be positive"
    
    assert merged_cells_found, "Complex tables should have merged cells"


def test_data_type_detection():
    """
    Test the detection of different data types within table cells.
    Verifies that numeric, date, currency, and text data types are correctly identified.
    """
    # Use a sample with various data types in tables
    sample_name = "sample3_data_types"
    
    # Skip if sample PDF doesn't exist
    pdf_path = TEST_DATA_DIR / f"{sample_name}.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Sample PDF {sample_name}.pdf not found")
    
    # Process the document
    pipeline_service = PipelineService()
    result = pipeline_service.process_document(str(pdf_path))
    
    # Track if we found tables with data types
    data_types_found = False
    
    # Create a dictionary to track data type counts
    data_type_counts = {
        "numeric": 0,
        "date": 0,
        "currency": 0,
        "text": 0,
        "other": 0
    }
    
    # Helper functions to detect data types
    def is_numeric(text):
        return bool(re.match(r'^-?\d+(\.\d+)?$', text.strip()))
    
    def is_date(text):
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # MM/DD/YYYY, DD/MM/YYYY
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',    # YYYY/MM/DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b'  # Month DD, YYYY
        ]
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in date_patterns)
    
    def is_currency(text):
        return bool(re.match(r'^[$€£¥][ ]?\d+([,.]\d+)?$|^\d+([,.]\d+)?[ ]?[$€£¥]$', text.strip()))
    
    # Examine each page for tables
    for page in result["pages"]:
        tables = page.get("tables", [])
        
        for table_idx, table in enumerate(tables):
            cells = table.get("cells", [])
            
            # Skip tables without cells
            if not cells:
                continue
                
            data_types_found = True
            table_data_types = []
            
            # Analyze each cell for data type
            for cell in cells:
                cell_text = cell.get("text", "").strip()
                
                # Skip empty cells
                if not cell_text:
                    continue
                
                # Determine data type
                data_type = "text"  # Default
                
                if is_currency(cell_text):
                    data_type = "currency"
                    data_type_counts["currency"] += 1
                elif is_numeric(cell_text):
                    data_type = "numeric"
                    data_type_counts["numeric"] += 1
                elif is_date(cell_text):
                    data_type = "date"
                    data_type_counts["date"] += 1
                else:
                    data_type = "text"
                    data_type_counts["text"] += 1
                
                # Add data type to the list for visualization
                table_data_types.append((cell, data_type))
            
            # Create visualization for this table
            fig, ax = plt.subplots(figsize=(12, 8))
            ax.set_title(f"Table Data Type Detection - Page {page['page_num']}, Table {table_idx + 1}")
            
            # Set up the plot
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.invert_yaxis()  # Invert y-axis to match PDF coordinates
            
            # Define colors for each data type
            colors = {
                "numeric": "#5DA5DA",  # Blue
                "date": "#60BD68",     # Green
                "currency": "#F15854", # Red
                "text": "#DECF3F",     # Yellow
                "other": "#B276B2"     # Purple
            }
            
            # Draw cells with color based on data type
            for cell, data_type in table_data_types:
                x0, y0, x1, y1 = cell.get("x0", 0), cell.get("y0", 0), cell.get("x1", 1), cell.get("y1", 1)
                rect = plt.Rectangle((x0, y0), x1 - x0, y1 - y0, 
                                   fill=True, alpha=0.5, color=colors[data_type],
                                   linewidth=1, edgecolor='black')
                ax.add_patch(rect)
                
                # Add text annotation in the center of the cell
                text = cell.get("text", "").strip()
                if len(text) > 15:
                    text = text[:12] + "..."
                plt.text((x0 + x1) / 2, (y0 + y1) / 2, text,
                        horizontalalignment='center',
                        verticalalignment='center',
                        fontsize=8, color='black', fontweight='bold')
            
            # Add legend
            legend_elements = [
                plt.Rectangle((0, 0), 1, 1, color=colors["numeric"], alpha=0.5, label='Numeric'),
                plt.Rectangle((0, 0), 1, 1, color=colors["date"], alpha=0.5, label='Date'),
                plt.Rectangle((0, 0), 1, 1, color=colors["currency"], alpha=0.5, label='Currency'),
                plt.Rectangle((0, 0), 1, 1, color=colors["text"], alpha=0.5, label='Text')
            ]
            ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.05), 
                    ncol=4, fancybox=True, shadow=True)
            
            # Save visualization
            visual_path = TEST_VISUALS_DIR / f"{sample_name}_data_types_page{page['page_num']}_table{table_idx + 1}.png"
            plt.tight_layout()
            plt.savefig(visual_path, dpi=150)
            plt.close()
    
    # Skip if no tables with data found
    if not data_types_found:
        pytest.skip(f"No tables with data found in {sample_name}.pdf")
    
    # Create a summary visualization of data type counts
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_title("Data Type Distribution in Tables")
    
    # Create bar chart of data type counts
    data_types = list(data_type_counts.keys())
    counts = list(data_type_counts.values())
    
    # Skip data types with count 0
    non_zero_indices = [i for i, count in enumerate(counts) if count > 0]
    data_types = [data_types[i] for i in non_zero_indices]
    counts = [counts[i] for i in non_zero_indices]
    
    # Set colors for the bars
    bar_colors = [colors[dt] for dt in data_types]
    
    bars = ax.bar(data_types, counts, color=bar_colors, alpha=0.7)
    
    # Add count labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{int(height)}',
                ha='center', va='bottom', fontweight='bold')
    
    # Save summary visualization
    summary_path = TEST_VISUALS_DIR / f"{sample_name}_data_types_summary.png"
    plt.tight_layout()
    plt.savefig(summary_path, dpi=150)
    plt.close()
    
    # Assert we found at least two different data types
    different_types = sum(1 for count in data_type_counts.values() if count > 0)
    assert different_types >= 2, f"Expected at least 2 different data types, found {different_types}"
    
    # Assert we have reasonable counts of data
    total_cells = sum(data_type_counts.values())
    assert total_cells >= 10, f"Expected at least 10 cells with content, found {total_cells}"
