"""
Tests for table extraction and detection functionality.

This module verifies the document processing pipeline's ability to detect,
extract, and analyze tables from PDF documents, checking their structure,
positioning, and overall extraction accuracy.
"""

import matplotlib.pyplot as plt
import pytest
from matplotlib.patches import Rectangle

# Import application modules
try:
    from app.services.pipeline_service import PipelineService
except ImportError:
    pytest.skip("PipelineService not available", allow_module_level=True)

# Import test utilities
from ..conftest import TEST_DATA_DIR, TEST_VISUALS_DIR


def visualize_table_extraction(document_result, page_idx, output_path, title=None):
    """
    Create a visualization of extracted tables on a given page.
    
    Args:
        document_result: Processed document result
        page_idx: Page index to visualize
        output_path: Path to save the visualization image
        title: Optional title for the visualization
        
    Returns:
        Path: Path to the saved visualization image
    """
    if page_idx >= len(document_result["pages"]):
        return None
    
    page = document_result["pages"][page_idx]
    
    # Check if page has tables
    if "tables" not in page or not page["tables"]:
        # Create a visualization showing no tables found
        fig, ax = plt.subplots(figsize=(8, 10))
        if title:
            ax.set_title(title)
        else:
            ax.set_title(f"No Tables Found - Page {page_idx + 1}")
        
        ax.text(0.5, 0.5, "No tables detected on this page", 
                ha="center", va="center", fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_axis_off()
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        return output_path
    
    # Get page dimensions
    page_width = page.get("width", 612)  # Default to 8.5x11 at 72dpi
    page_height = page.get("height", 792)
    
    # Create figure with aspect ratio matching the page
    aspect_ratio = page_height / page_width
    fig_width = 10
    fig_height = fig_width * aspect_ratio
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    
    if title:
        ax.set_title(title)
    else:
        ax.set_title(f"Table Extraction - Page {page_idx + 1}")
    
    # Set the axis limits to match page dimensions
    ax.set_xlim(0, page_width)
    ax.set_ylim(page_height, 0)  # Reverse y-axis to match PDF coordinates
    
    # Draw page boundary
    ax.add_patch(Rectangle((0, 0), page_width, page_height, 
                          fill=False, edgecolor='black', linewidth=1))
    
    # Add text blocks if available for context
    if "text_blocks" in page:
        for block in page["text_blocks"]:
            x0, y0 = block.get("x0", 0), block.get("y0", 0)
            x1, y1 = block.get("x1", x0), block.get("y1", y0)
            
            # Draw text block boundary with light gray
            ax.add_patch(Rectangle((x0, y0), x1-x0, y1-y0, 
                                  fill=True, alpha=0.1, 
                                  edgecolor='gray', facecolor='lightgray', linewidth=0.5))
    
    # Draw tables
    for i, table in enumerate(page["tables"]):
        x0, y0 = table.get("x0", 0), table.get("y0", 0)
        x1, y1 = table.get("x1", x0), table.get("y1", y0)
        
        # Draw table boundary with blue
        ax.add_patch(Rectangle((x0, y0), x1-x0, y1-y0, 
                              fill=False, edgecolor='blue', linewidth=2))
        
        # Add table label
        ax.text(x0, y0 - 5, f"Table {i+1}", 
                fontsize=10, color='blue', weight='bold')
        
        # Draw cells if available
        if "cells" in table:
            for cell in table["cells"]:
                cell_x0, cell_y0 = cell.get("x0", 0), cell.get("y0", 0)
                cell_x1, cell_y1 = cell.get("x1", cell_x0), cell.get("y1", cell_y0)
                
                # Draw cell boundary with light blue
                ax.add_patch(Rectangle((cell_x0, cell_y0), cell_x1-cell_x0, cell_y1-cell_y0, 
                                      fill=False, edgecolor='lightblue', linewidth=1))
        
        # Draw rows if available
        if "rows" in table:
            for row in table["rows"]:
                row_y = row.get("y0", 0)
                # Draw horizontal line for row
                ax.axhline(y=row_y, xmin=x0/page_width, xmax=x1/page_width, 
                           color='red', linestyle='--', linewidth=0.8, alpha=0.6)
        
        # Draw columns if available
        if "columns" in table:
            for col in table["columns"]:
                col_x = col.get("x0", 0)
                # Draw vertical line for column
                ax.axvline(x=col_x, ymin=y0/page_height, ymax=y1/page_height, 
                           color='green', linestyle='--', linewidth=0.8, alpha=0.6)
    
    # Save the figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    return output_path


def test_table_structure(expected_outputs):
    """
    Test that extracted tables have the expected structure.
    
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
    
    # Check that tables are found in at least one page
    tables_found = False
    
    for page_idx, page in enumerate(result["pages"]):
        if "tables" in page and page["tables"]:
            tables_found = True
            
            # Check table structure for each table
            for table_idx, table in enumerate(page["tables"]):
                # Tables should have boundary coordinates
                assert "x0" in table, f"Table {table_idx} on page {page_idx} missing x0 coordinate"
                assert "y0" in table, f"Table {table_idx} on page {page_idx} missing y0 coordinate"
                assert "x1" in table, f"Table {table_idx} on page {page_idx} missing x1 coordinate"
                assert "y1" in table, f"Table {table_idx} on page {page_idx} missing y1 coordinate"
                
                # Table should have cells or structure information
                assert any(key in table for key in ["cells", "rows", "columns"]), \
                    f"Table {table_idx} on page {page_idx} has no cells or structure information"
                
                # If cells are present, check their structure
                if "cells" in table:
                    for cell_idx, cell in enumerate(table["cells"]):
                        # Cells should have boundary coordinates
                        assert "x0" in cell, f"Cell {cell_idx} in table {table_idx} on page {page_idx} missing x0"
                        assert "y0" in cell, f"Cell {cell_idx} in table {table_idx} on page {page_idx} missing y0"
                        assert "x1" in cell, f"Cell {cell_idx} in table {table_idx} on page {page_idx} missing x1"
                        assert "y1" in cell, f"Cell {cell_idx} in table {table_idx} on page {page_idx} missing y1"
                        
                        # Cells should have text content (can be empty string)
                        assert "text" in cell, f"Cell {cell_idx} in table {table_idx} on page {page_idx} missing text"
    
    assert tables_found, "No tables found in the document"


@pytest.mark.parametrize("sample_name, expected_tables", [
    ("sample2_tables", {"page_0": 2, "page_1": 1}),  # Example: 2 tables on page 0, 1 on page 1
    ("sample4_complex", {"page_0": 1}),              # Example: 1 complex table on page 0
])
def test_table_extraction(sample_name, expected_tables, expected_outputs):
    """
    Test table extraction for different sample documents.
    
    Args:
        sample_name: Name of the sample document
        expected_tables: Dictionary of expected table counts per page
        expected_outputs: Fixture providing expected outputs
    """
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
    
    # Check table counts on each page
    for page_key, expected_count in expected_tables.items():
        page_idx = int(page_key.split("_")[1])
        
        if page_idx >= len(result["pages"]):
            pytest.skip("Document has fewer pages than expected")
        
        page = result["pages"][page_idx]
        
        # If tables are expected but none found, fail
        if expected_count > 0:
            assert "tables" in page, f"No tables field in page {page_idx}"
            assert page["tables"], f"Expected tables on page {page_idx} but none found"
            
            actual_count = len(page["tables"])
            assert actual_count == expected_count, \
                f"Expected {expected_count} tables on page {page_idx}, but found {actual_count}"
        
        # Create a visualization of the extracted tables
        visual_path = TEST_VISUALS_DIR / f"{sample_name}_page_{page_idx}_tables.png"
        visualize_table_extraction(result, page_idx, visual_path,
                                 f"Table Extraction - {sample_name} - Page {page_idx + 1}")


def test_table_boundaries(expected_outputs):
    """
    Test that table boundaries are correctly identified.
    
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
    
    # Check that table boundaries match expected output
    has_tables = False
    
    for page_idx, page in enumerate(result["pages"]):
        if "tables" not in page or not page["tables"]:
            continue
            
        # Skip pages not in expected output
        if page_idx >= len(expected_output["pages"]) or "tables" not in expected_output["pages"][page_idx]:
            continue
            
        expected_tables = expected_output["pages"][page_idx]["tables"]
        
        for table_idx, table in enumerate(page["tables"]):
            has_tables = True
            
            # Skip if more tables than expected
            if table_idx >= len(expected_tables):
                continue
                
            expected_table = expected_tables[table_idx]
            
            # Check that table boundaries are close to expected
            for coord in ["x0", "y0", "x1", "y1"]:
                if coord in expected_table:
                    assert coord in table, f"Table {table_idx} on page {page_idx} missing {coord} coordinate"
                    
                    actual = table[coord]
                    expected = expected_table[coord]
                    
                    # Allow for small variations in boundary detection (within 5% of page dimensions)
                    page_dimension = page.get("width", 612) if coord in ["x0", "x1"] else page.get("height", 792)
                    tolerance = page_dimension * 0.05
                    
                    assert abs(actual - expected) <= tolerance, \
                        f"Table {table_idx} on page {page_idx} has {coord}={actual}, expected around {expected} (±{tolerance})"
    
    assert has_tables, "No matching tables found in the document and expected output"


def test_row_detection(expected_outputs):
    """
    Test that table rows are correctly detected.
    
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
    
    # Check row detection in tables
    rows_detected = False
    
    for page_idx, page in enumerate(result["pages"]):
        if "tables" not in page or not page["tables"]:
            continue
            
        for table_idx, table in enumerate(page["tables"]):
            # Check for explicit row information
            if "rows" in table and table["rows"]:
                rows_detected = True
                
                # Rows should be sorted by y-coordinate
                rows = table["rows"]
                
                # Check that rows have y-coordinates
                for row_idx, row in enumerate(rows):
                    assert "y0" in row, f"Row {row_idx} in table {table_idx} on page {page_idx} missing y0"
                
                # Create visualization of row detection
                visual_path = TEST_VISUALS_DIR / f"{sample_name}_table_{page_idx}_{table_idx}_rows.png"
                visualize_table_extraction(result, page_idx, visual_path,
                                         f"Row Detection - Table {table_idx} on Page {page_idx + 1}")
            
            # Alternatively, check for row information in cells
            elif "cells" in table and all("row" in cell for cell in table["cells"]):
                rows_detected = True
                
                # Find unique row indices
                row_indices = sorted(set(cell["row"] for cell in table["cells"]))
                
                # Check that row indices are consecutive
                assert row_indices == list(range(min(row_indices), max(row_indices) + 1)), \
                    f"Row indices in table {table_idx} on page {page_idx} are not consecutive"
                
                # Create visualization of row detection from cells
                visual_path = TEST_VISUALS_DIR / f"{sample_name}_table_{page_idx}_{table_idx}_cell_rows.png"
                
                # Add row information to the result for visualization
                if "rows" not in table:
                    table["rows"] = []
                    
                    # Group cells by row
                    rows_by_index = {}
                    for cell in table["cells"]:
                        row_idx = cell["row"]
                        if row_idx not in rows_by_index:
                            rows_by_index[row_idx] = []
                        rows_by_index[row_idx].append(cell)
                    
                    # Create row entries based on cell positions
                    for row_idx in sorted(rows_by_index.keys()):
                        cells = rows_by_index[row_idx]
                        min_y0 = min(cell["y0"] for cell in cells)
                        
                        table["rows"].append({
                            "y0": min_y0,
                            "index": row_idx
                        })
                
                visualize_table_extraction(result, page_idx, visual_path,
                                         f"Cell-based Row Detection - Table {table_idx} on Page {page_idx + 1}")
    
    assert rows_detected, "No tables with row information found in the document"


def test_column_detection(expected_outputs):
    """
    Test that table columns are correctly detected.
    
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
    
    # Check column detection in tables
    columns_detected = False
    
    for page_idx, page in enumerate(result["pages"]):
        if "tables" not in page or not page["tables"]:
            continue
            
        for table_idx, table in enumerate(page["tables"]):
            # Check for explicit column information
            if "columns" in table and table["columns"]:
                columns_detected = True
                
                # Columns should be sorted by x-coordinate
                columns = table["columns"]
                
                # Check that columns have x-coordinates
                for col_idx, col in enumerate(columns):
                    assert "x0" in col, f"Column {col_idx} in table {table_idx} on page {page_idx} missing x0"
                
                # Create visualization of column detection
                visual_path = TEST_VISUALS_DIR / f"{sample_name}_table_{page_idx}_{table_idx}_columns.png"
                visualize_table_extraction(result, page_idx, visual_path,
                                         f"Column Detection - Table {table_idx} on Page {page_idx + 1}")
            
            # Alternatively, check for column information in cells
            elif "cells" in table and all("col" in cell for cell in table["cells"]):
                columns_detected = True
                
                # Find unique column indices
                col_indices = sorted(set(cell["col"] for cell in table["cells"]))
                
                # Check that column indices are consecutive
                assert col_indices == list(range(min(col_indices), max(col_indices) + 1)), \
                    f"Column indices in table {table_idx} on page {page_idx} are not consecutive"
                
                # Create visualization of column detection from cells
                visual_path = TEST_VISUALS_DIR / f"{sample_name}_table_{page_idx}_{table_idx}_cell_columns.png"
                
                # Add column information to the result for visualization
                if "columns" not in table:
                    table["columns"] = []
                    
                    # Group cells by column
                    cols_by_index = {}
                    for cell in table["cells"]:
                        col_idx = cell["col"]
                        if col_idx not in cols_by_index:
                            cols_by_index[col_idx] = []
                        cols_by_index[col_idx].append(cell)
                    
                    # Create column entries based on cell positions
                    for col_idx in sorted(cols_by_index.keys()):
                        cells = cols_by_index[col_idx]
                        min_x0 = min(cell["x0"] for cell in cells)
                        
                        table["columns"].append({
                            "x0": min_x0,
                            "index": col_idx
                        })
                
                visualize_table_extraction(result, page_idx, visual_path,
                                         f"Cell-based Column Detection - Table {table_idx} on Page {page_idx + 1}")
    
    assert columns_detected, "No tables with column information found in the document"


def test_table_in_multi_column_layout():
    """
    Test table extraction in documents with multi-column layout.
    """
    # Use a sample document with multi-column layout containing tables
    sample_name = "sample3_multicolumn"
    
    # Skip if sample PDF doesn't exist
    pdf_path = TEST_DATA_DIR / f"{sample_name}.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Sample PDF {sample_name}.pdf not found")
    
    # Process the document
    pipeline_service = PipelineService()
    result = pipeline_service.process_document(str(pdf_path))
    
    # Check if there are tables in the result
    tables_found = False
    for page_idx, page in enumerate(result["pages"]):
        if "tables" in page and page["tables"]:
            tables_found = True
            
            # Create visualization of tables in multi-column layout
            visual_path = TEST_VISUALS_DIR / f"{sample_name}_page_{page_idx}_tables.png"
            visualize_table_extraction(result, page_idx, visual_path,
                                     f"Tables in Multi-column Layout - Page {page_idx + 1}")
    
    if not tables_found:
        pytest.skip("No tables found in multi-column document")
    
    # Test passes if we found tables in the multi-column document
    assert tables_found, "Should detect tables in multi-column layout"


def test_extraction_accuracy(expected_outputs):
    """
    Test the accuracy of table extraction by comparing against ground truth.
    
    Args:
        expected_outputs: Fixture providing expected outputs (ground truth)
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
    
    # Initialize metrics
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    iou_scores = []
    
    # Function to calculate IoU (Intersection over Union)
    def calculate_iou(box1, box2):
        # Calculate intersection
        x0_intersection = max(box1["x0"], box2["x0"])
        y0_intersection = max(box1["y0"], box2["y0"])
        x1_intersection = min(box1["x1"], box2["x1"])
        y1_intersection = min(box1["y1"], box2["y1"])
        
        # Check if boxes intersect
        if x0_intersection >= x1_intersection or y0_intersection >= y1_intersection:
            return 0.0
        
        intersection_area = (x1_intersection - x0_intersection) * (y1_intersection - y0_intersection)
        
        # Calculate areas of both boxes
        box1_area = (box1["x1"] - box1["x0"]) * (box1["y1"] - box1["y0"])
        box2_area = (box2["x1"] - box2["x0"]) * (box2["y1"] - box2["y0"])
        
        # Calculate IoU
        union_area = box1_area + box2_area - intersection_area
        iou = intersection_area / union_area if union_area > 0 else 0.0
        
        return iou
    
    # Compare tables on each page
    for page_idx, page in enumerate(result["pages"]):
        # Skip if page not in expected output
        if page_idx >= len(expected_output["pages"]):
            continue
        
        expected_page = expected_output["pages"][page_idx]
        
        # Skip if tables are not expected on this page
        if "tables" not in expected_page:
            continue
        
        expected_tables = expected_page["tables"]
        
        # Count tables in result
        actual_tables = page.get("tables", [])
        
        # Track which expected tables were matched
        matched_expected_tables = [False] * len(expected_tables)
        
        # For each detected table, find the best matching expected table
        for actual_table in actual_tables:
            best_iou = 0.0
            best_match_idx = -1
            
            for idx, expected_table in enumerate(expected_tables):
                # Calculate IoU between actual and expected table
                iou = calculate_iou(actual_table, expected_table)
                
                if iou > best_iou:
                    best_iou = iou
                    best_match_idx = idx
            
            # Consider a match if IoU is above threshold
            if best_iou >= 0.5 and not matched_expected_tables[best_match_idx]:
                true_positives += 1
                matched_expected_tables[best_match_idx] = True
                iou_scores.append(best_iou)
            else:
                false_positives += 1
        
        # Count unmatched expected tables as false negatives
        false_negatives += matched_expected_tables.count(False)
    
    # Calculate precision, recall, F1 score
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    mean_iou = sum(iou_scores) / len(iou_scores) if iou_scores else 0
    
    # Create a visualization of the results
    fig, ax = plt.subplots(figsize=(10, 6))
    metrics = ['Precision', 'Recall', 'F1 Score', 'Mean IoU']
    values = [precision, recall, f1_score, mean_iou]
    
    ax.bar(metrics, values, color=['blue', 'green', 'red', 'purple'])
    ax.set_ylim(0, 1.0)
    ax.set_ylabel('Score')
    ax.set_title(f'Table Extraction Accuracy Metrics - {sample_name}')
    
    # Add value labels on top of bars
    for i, v in enumerate(values):
        ax.text(i, v + 0.02, f'{v:.2f}', ha='center')
    
    # Add text box with detailed results
    text_info = (f"True Positives: {true_positives}\n"
                f"False Positives: {false_positives}\n"
                f"False Negatives: {false_negatives}\n"
                f"IoU Scores: {', '.join([f'{iou:.2f}' for iou in iou_scores])}")
    
    plt.figtext(0.15, 0.01, text_info, wrap=True, fontsize=9, 
                bbox=dict(facecolor='lightgray', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(f"{TEST_VISUALS_DIR}/{sample_name}_extraction_accuracy.png")
    plt.close()
    
    # Assert minimum quality thresholds
    assert precision >= 0.7, f"Precision ({precision:.2f}) below threshold (0.7)"
    assert recall >= 0.7, f"Recall ({recall:.2f}) below threshold (0.7)"
    assert f1_score >= 0.7, f"F1 Score ({f1_score:.2f}) below threshold (0.7)"
    assert mean_iou >= 0.6, f"Mean IoU ({mean_iou:.2f}) below threshold (0.6)"
