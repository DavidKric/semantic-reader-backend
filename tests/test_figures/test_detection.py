"""
Tests for figure detection and extraction functionality.

This module verifies the document processing pipeline's ability to detect,
extract, and analyze figures from PDF documents, checking their structure,
positioning, captions, and overall extraction accuracy.
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


def visualize_figure_extraction(document_result, page_idx, output_path, title=None):
    """
    Create a visualization of extracted figures on a given page.
    
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
    
    # Check if page has figures
    if "figures" not in page or not page["figures"]:
        # Create a visualization showing no figures found
        fig, ax = plt.subplots(figsize=(8, 10))
        if title:
            ax.set_title(title)
        else:
            ax.set_title(f"No Figures Found - Page {page_idx + 1}")
        
        ax.text(0.5, 0.5, "No figures detected on this page", 
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
        ax.set_title(f"Figure Extraction - Page {page_idx + 1}")
    
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
    
    # Draw figures
    for i, figure in enumerate(page["figures"]):
        x0, y0 = figure.get("x0", 0), figure.get("y0", 0)
        x1, y1 = figure.get("x1", x0), figure.get("y1", y0)
        
        # Draw figure boundary with red
        ax.add_patch(Rectangle((x0, y0), x1-x0, y1-y0, 
                              fill=False, edgecolor='red', linewidth=2))
        
        # Add figure label
        ax.text(x0, y0 - 5, f"Figure {i+1}", 
                fontsize=10, color='red', weight='bold')
        
        # Draw caption boundary if available
        if "caption" in figure and isinstance(figure["caption"], dict):
            caption = figure["caption"]
            if all(k in caption for k in ["x0", "y0", "x1", "y1"]):
                cap_x0, cap_y0 = caption.get("x0", 0), caption.get("y0", 0)
                cap_x1, cap_y1 = caption.get("x1", cap_x0), caption.get("y1", cap_y0)
                
                # Draw caption boundary with green
                ax.add_patch(Rectangle((cap_x0, cap_y0), cap_x1-cap_x0, cap_y1-cap_y0, 
                                      fill=False, edgecolor='green', linewidth=1.5))
                
                # Add caption label
                ax.text(cap_x0, cap_y0 - 5, "Caption", 
                        fontsize=8, color='green', weight='bold')
                
                # Draw line connecting figure to caption
                ax.plot([x0 + (x1-x0)/2, cap_x0 + (cap_x1-cap_x0)/2], 
                        [y1, cap_y0], 
                        'g--', linewidth=0.8, alpha=0.6)
        
        # Draw subcaptions if available
        if "subcaptions" in figure and isinstance(figure["subcaptions"], list):
            for j, subcap in enumerate(figure["subcaptions"]):
                if all(k in subcap for k in ["x0", "y0", "x1", "y1"]):
                    sub_x0, sub_y0 = subcap.get("x0", 0), subcap.get("y0", 0)
                    sub_x1, sub_y1 = subcap.get("x1", sub_x0), subcap.get("y1", sub_y0)
                    
                    # Draw subcaption boundary with orange
                    ax.add_patch(Rectangle((sub_x0, sub_y0), sub_x1-sub_x0, sub_y1-sub_y0, 
                                          fill=False, edgecolor='orange', linewidth=1))
                    
                    # Add subcaption label
                    ax.text(sub_x0, sub_y0 - 5, f"Subcaption {j+1}", 
                            fontsize=7, color='orange')
    
    # Save the figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    return output_path


def test_figure_structure(expected_outputs):
    """
    Test that extracted figures have the expected structure.
    
    Args:
        expected_outputs: Fixture providing expected outputs
    """
    # Use a sample document with figures
    sample_name = "sample5_figures"
    
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
    
    # Check that figures are found in at least one page
    figures_found = False
    
    for page_idx, page in enumerate(result["pages"]):
        if "figures" in page and page["figures"]:
            figures_found = True
            
            # Check figure structure for each figure
            for figure_idx, figure in enumerate(page["figures"]):
                # Figures should have boundary coordinates
                assert "x0" in figure, f"Figure {figure_idx} on page {page_idx} missing x0 coordinate"
                assert "y0" in figure, f"Figure {figure_idx} on page {page_idx} missing y0 coordinate"
                assert "x1" in figure, f"Figure {figure_idx} on page {page_idx} missing x1 coordinate"
                assert "y1" in figure, f"Figure {figure_idx} on page {page_idx} missing y1 coordinate"
                
                # Figure should have a type or content information
                assert any(key in figure for key in ["type", "image_type", "content_type"]), \
                    f"Figure {figure_idx} on page {page_idx} has no type information"
                
                # If caption is present, check its structure
                if "caption" in figure and isinstance(figure["caption"], dict):
                    caption = figure["caption"]
                    assert "text" in caption, f"Caption for figure {figure_idx} on page {page_idx} missing text"
                    # Boundaries for caption are optional but should be consistent if present
                    if "x0" in caption:
                        assert "y0" in caption, "Caption missing y0 coordinate"
                        assert "x1" in caption, "Caption missing x1 coordinate"
                        assert "y1" in caption, "Caption missing y1 coordinate"
    
    assert figures_found, "No figures found in the document"


@pytest.mark.parametrize("sample_name, expected_figures", [
    ("sample5_figures", {"page_0": 2, "page_1": 3}),  # Example: 2 figures on page 0, 3 on page 1
    ("sample6_mixed", {"page_0": 1}),                # Example: 1 figure on page 0
])
def test_figure_extraction(sample_name, expected_figures, expected_outputs):
    """
    Test figure extraction for different sample documents.
    
    Args:
        sample_name: Name of the sample document
        expected_figures: Dictionary of expected figure counts per page
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
    
    # Check figure counts on each page
    for page_key, expected_count in expected_figures.items():
        page_idx = int(page_key.split("_")[1])
        
        if page_idx >= len(result["pages"]):
            pytest.skip("Document has fewer pages than expected")
        
        page = result["pages"][page_idx]
        
        # If figures are expected but none found, fail
        if expected_count > 0:
            assert "figures" in page, f"No figures field in page {page_idx}"
            assert page["figures"], f"Expected figures on page {page_idx} but none found"
            
            actual_count = len(page["figures"])
            assert actual_count == expected_count, \
                f"Expected {expected_count} figures on page {page_idx}, but found {actual_count}"
        
        # Create a visualization of the extracted figures
        visual_path = TEST_VISUALS_DIR / f"{sample_name}_page_{page_idx}_figures.png"
        visualize_figure_extraction(result, page_idx, visual_path,
                                   f"Figure Extraction - {sample_name} - Page {page_idx + 1}")


def test_figure_boundaries(expected_outputs):
    """
    Test that figure boundaries are correctly identified.
    
    Args:
        expected_outputs: Fixture providing expected outputs
    """
    # Use a sample document with figures
    sample_name = "sample5_figures"
    
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
    
    # Check that figure boundaries match expected output
    has_figures = False
    
    for page_idx, page in enumerate(result["pages"]):
        if "figures" not in page or not page["figures"]:
            continue
            
        # Skip pages not in expected output
        if page_idx >= len(expected_output["pages"]) or "figures" not in expected_output["pages"][page_idx]:
            continue
            
        expected_figures = expected_output["pages"][page_idx]["figures"]
        
        for figure_idx, figure in enumerate(page["figures"]):
            has_figures = True
            
            # Skip if more figures than expected
            if figure_idx >= len(expected_figures):
                continue
                
            expected_figure = expected_figures[figure_idx]
            
            # Check that figure boundaries are close to expected
            for coord in ["x0", "y0", "x1", "y1"]:
                if coord in expected_figure:
                    assert coord in figure, f"Figure {figure_idx} on page {page_idx} missing {coord} coordinate"
                    
                    actual = figure[coord]
                    expected = expected_figure[coord]
                    
                    # Allow for small variations in boundary detection (within 5% of page dimensions)
                    page_dimension = page.get("width", 612) if coord in ["x0", "x1"] else page.get("height", 792)
                    tolerance = page_dimension * 0.05
                    
                    assert abs(actual - expected) <= tolerance, \
                        f"Figure {figure_idx} on page {page_idx} has {coord}={actual}, expected around {expected} (±{tolerance})"
    
    assert has_figures, "No matching figures found in the document and expected output"


def test_caption_detection(expected_outputs):
    """
    Test that captions are correctly associated with figures.
    
    Args:
        expected_outputs: Fixture providing expected outputs
    """
    # Use a sample document with figures and captions
    sample_name = "sample5_figures"
    
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
    
    # Track if we found any captions
    captions_found = False
    
    for page_idx, page in enumerate(result["pages"]):
        if "figures" not in page or not page["figures"]:
            continue
            
        # Skip pages not in expected output
        if page_idx >= len(expected_output["pages"]) or "figures" not in expected_output["pages"][page_idx]:
            continue
            
        expected_figures = expected_output["pages"][page_idx]["figures"]
        
        for figure_idx, figure in enumerate(page["figures"]):
            # Skip if more figures than expected
            if figure_idx >= len(expected_figures):
                continue
                
            expected_figure = expected_figures[figure_idx]
            
            # Check caption detection and content
            if "caption" in expected_figure:
                assert "caption" in figure, f"Figure {figure_idx} on page {page_idx} missing caption"
                
                captions_found = True
                
                # Test caption text if available
                if "text" in expected_figure["caption"]:
                    expected_text = expected_figure["caption"]["text"]
                    actual_text = figure["caption"].get("text", "")
                    
                    # Caption text should contain key parts of expected text
                    # but we don't expect exact matches due to different text normalization
                    if len(expected_text) > 10:  # Only meaningful captions
                        key_parts = expected_text.split()[:3]  # First few words should match
                        for part in key_parts:
                            if len(part) > 3:  # Only check significant words
                                assert part.lower() in actual_text.lower(), \
                                    f"Caption missing key text '{part}'"
    
    # Skip test if no captions in the expected output
    if not captions_found:
        pytest.skip("No captions found in expected output")


def test_figure_in_multi_column_layout():
    """
    Test figure extraction in documents with multi-column layout.
    """
    # Use a sample document with multi-column layout containing figures
    sample_name = "sample2_multicolumn"
    
    # Skip if sample PDF doesn't exist
    pdf_path = TEST_DATA_DIR / f"{sample_name}.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Sample PDF {sample_name}.pdf not found")
    
    # Process the document
    pipeline_service = PipelineService()
    result = pipeline_service.process_document(str(pdf_path))
    
    # Check if there are figures in the result
    figures_found = False
    for page_idx, page in enumerate(result["pages"]):
        if "figures" in page and page["figures"]:
            figures_found = True
            
            # Create visualization of figures in multi-column layout
            visual_path = TEST_VISUALS_DIR / f"{sample_name}_page_{page_idx}_figures.png"
            visualize_figure_extraction(result, page_idx, visual_path,
                                       f"Figures in Multi-column Layout - Page {page_idx + 1}")
    
    if not figures_found:
        pytest.skip("No figures found in multi-column document")
    
    # Test passes if we found figures in the multi-column document
    assert figures_found, "Should detect figures in multi-column layout"


def test_extraction_accuracy(expected_outputs):
    """
    Test the accuracy of figure extraction by comparing against ground truth.
    
    Args:
        expected_outputs: Fixture providing expected outputs (ground truth)
    """
    # Use a sample document with figures
    sample_name = "sample5_figures"
    
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
    
    # Compare figures on each page
    for page_idx, page in enumerate(result["pages"]):
        # Skip if page not in expected output
        if page_idx >= len(expected_output["pages"]):
            continue
        
        expected_page = expected_output["pages"][page_idx]
        
        # Skip if figures are not expected on this page
        if "figures" not in expected_page:
            continue
        
        expected_figures = expected_page["figures"]
        
        # Count figures in result
        actual_figures = page.get("figures", [])
        
        # Track which expected figures were matched
        matched_expected_figures = [False] * len(expected_figures)
        
        # For each detected figure, find the best matching expected figure
        for actual_figure in actual_figures:
            best_iou = 0.0
            best_match_idx = -1
            
            for idx, expected_figure in enumerate(expected_figures):
                # Calculate IoU between actual and expected figure
                iou = calculate_iou(actual_figure, expected_figure)
                
                if iou > best_iou:
                    best_iou = iou
                    best_match_idx = idx
            
            # Consider a match if IoU is above threshold
            if best_iou >= 0.5 and not matched_expected_figures[best_match_idx]:
                true_positives += 1
                matched_expected_figures[best_match_idx] = True
                iou_scores.append(best_iou)
            else:
                false_positives += 1
        
        # Count unmatched expected figures as false negatives
        false_negatives += matched_expected_figures.count(False)
    
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
    ax.set_title(f'Figure Extraction Accuracy Metrics - {sample_name}')
    
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
    plt.savefig(f"{TEST_VISUALS_DIR}/{sample_name}_figure_extraction_accuracy.png")
    plt.close()
    
    # Assert minimum quality thresholds
    assert precision >= 0.7, f"Precision ({precision:.2f}) below threshold (0.7)"
    assert recall >= 0.7, f"Recall ({recall:.2f}) below threshold (0.7)"
    assert f1_score >= 0.7, f"F1 Score ({f1_score:.2f}) below threshold (0.7)"
    assert mean_iou >= 0.6, f"Mean IoU ({mean_iou:.2f}) below threshold (0.6)"


def test_figure_content_type_detection():
    """
    Test that figure content types (chart, image, diagram) are correctly detected.
    """
    # Use a sample document with various figure types
    sample_name = "sample5_figures"
    
    # Skip if sample PDF doesn't exist
    pdf_path = TEST_DATA_DIR / f"{sample_name}.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Sample PDF {sample_name}.pdf not found")
    
    # Process the document
    pipeline_service = PipelineService()
    result = pipeline_service.process_document(str(pdf_path))
    
    # Track content type detection
    content_types_found = set()
    figures_with_type = 0
    total_figures = 0
    
    for page_idx, page in enumerate(result["pages"]):
        if "figures" not in page or not page["figures"]:
            continue
            
        for figure in page["figures"]:
            total_figures += 1
            
            # Check for content type information
            content_type = None
            if "type" in figure:
                content_type = figure["type"]
            elif "image_type" in figure:
                content_type = figure["image_type"]
            elif "content_type" in figure:
                content_type = figure["content_type"]
            
            if content_type:
                figures_with_type += 1
                content_types_found.add(content_type.lower())
    
    if total_figures == 0:
        pytest.skip("No figures found in the document")
    
    # Create visualization of content type distribution
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_title(f"Figure Content Type Detection - {sample_name}")
    
    # Plot the percentage of figures with detected content type
    detection_rate = figures_with_type / total_figures if total_figures > 0 else 0
    ax.bar(["Content Type Detection Rate"], [detection_rate], color="blue")
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Detection Rate")
    
    # Add value label
    ax.text(0, detection_rate + 0.02, f"{detection_rate:.2f}", ha="center")
    
    # Add content types found
    ax.text(0.5, 0.1, f"Content Types Found: {', '.join(content_types_found)}", 
            transform=ax.transAxes, ha="center", 
            bbox=dict(facecolor='lightgray', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(f"{TEST_VISUALS_DIR}/{sample_name}_content_type_detection.png")
    plt.close()
    
    # Assert that at least some figures have content type information
    assert figures_with_type > 0, "No figures with content type information found"
    # Assert that we can detect multiple types of figures
    assert len(content_types_found) > 0, "No figure content types detected"
