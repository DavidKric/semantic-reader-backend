"""
Tests for document visualization and parsing comparison.

This test suite:
1. Converts sample PDFs using the DocumentProcessingService
2. Generates visualizations at different levels (char, word, line)
3. Creates HTML reports with side-by-side comparisons
4. Integrates with pytest-html for better reporting
"""

import os
import json
import pytest
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any

# Import templates and report generation utilities
from tests.templates.report_generator import (
    generate_visualization_report,
    copy_report_assets_to_pytest_html,
    attach_report_to_pytest
)

# Import visualization utilities
try:
    from src.papermage_docling.visualizers.docling_visual import DoclingVisualizer
    DOCLING_VISUAL_AVAILABLE = True
except ImportError:
    DOCLING_VISUAL_AVAILABLE = False
    logging.warning("DoclingVisualizer not available. Some tests will be skipped.")

# Import document processing service
try:
    from src.papermage_docling.services.document_processing import DocumentProcessingService
    DOCUMENT_PROCESSING_AVAILABLE = True
except ImportError:
    DOCUMENT_PROCESSING_AVAILABLE = False
    logging.warning("DocumentProcessingService not available. Tests will be limited.")

# Define test data path - customize based on your project structure
TEST_DATA_DIR = Path(__file__).parent / "data" / "data"
TEST_OUTPUT_DIR = Path(__file__).parent / "test_outputs" / "visualizations"
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_sample_pdfs(category: Optional[str] = None) -> List[Path]:
    """
    Get paths to sample PDF files for testing.
    
    Args:
        category: Optional category filter (simple, multicolumn, tables)
        
    Returns:
        List of paths to sample PDF files
    """
    if not TEST_DATA_DIR.exists():
        pytest.skip(f"Test data directory not found: {TEST_DATA_DIR}")
    
    if category:
        pdf_pattern = f"sample*_{category}.pdf"
    else:
        pdf_pattern = "sample*.pdf"
    
    sample_pdfs = list(TEST_DATA_DIR.glob(pdf_pattern))
    
    if not sample_pdfs:
        pytest.skip(f"No sample PDFs found matching pattern: {pdf_pattern}")
    
    return sample_pdfs


def clean_previous_outputs(pdf_path: Path) -> None:
    """Remove previous test outputs for the given PDF."""
    base_name = pdf_path.stem
    
    # Remove visualization images
    for file_pattern in [f"{base_name}*_char_*.png", f"{base_name}*_word_*.png", 
                        f"{base_name}*_line_*.png", f"{base_name}*_original_*.png"]:
        for file_path in TEST_OUTPUT_DIR.glob(file_pattern):
            try:
                file_path.unlink()
            except Exception as e:
                logging.warning(f"Failed to remove {file_path}: {e}")
    
    # Remove report
    report_path = TEST_OUTPUT_DIR.parent / "reports" / f"{base_name}_visualization_report.html"
    if report_path.exists():
        try:
            report_path.unlink()
        except Exception as e:
            logging.warning(f"Failed to remove {report_path}: {e}")


def visualize_document(pdf_path: Path, doc_data: Dict[str, Any]) -> Dict[str, Dict[int, str]]:
    """
    Generate visualizations for a document.
    
    Args:
        pdf_path: Path to the original PDF file
        doc_data: Document data structure
        
    Returns:
        Dictionary mapping visualization types to page numbers and file paths
    """
    base_name = pdf_path.stem
    visualization_paths = {
        "original": {},
        "char": {},
        "word": {},
        "line": {}
    }
    
    if not DOCLING_VISUAL_AVAILABLE:
        logging.warning("DoclingVisualizer not available. Skipping visualization generation.")
        return visualization_paths
    
    # Create visualizer
    visualizer = DoclingVisualizer()
    
    for page_idx, page_data in enumerate(doc_data.get("pages", [])):
        page_num = page_idx + 1
        
        # Generate original page visualization if possible
        try:
            original_path = TEST_OUTPUT_DIR / f"{base_name}_original_{page_num}.png"
            visualizer.visualize_original_page(page_data, output_path=str(original_path))
            visualization_paths["original"][page_num] = str(original_path)
        except Exception as e:
            logging.warning(f"Failed to visualize original page {page_num}: {e}")
        
        # Generate character-level visualization
        try:
            char_path = TEST_OUTPUT_DIR / f"{base_name}_char_{page_num}.png"
            visualizer.visualize_characters(page_data, output_path=str(char_path))
            visualization_paths["char"][page_num] = str(char_path)
        except Exception as e:
            logging.warning(f"Failed to visualize characters for page {page_num}: {e}")
        
        # Generate word-level visualization
        try:
            word_path = TEST_OUTPUT_DIR / f"{base_name}_word_{page_num}.png"
            visualizer.visualize_words(page_data, output_path=str(word_path))
            visualization_paths["word"][page_num] = str(word_path)
        except Exception as e:
            logging.warning(f"Failed to visualize words for page {page_num}: {e}")
        
        # Generate line-level visualization
        try:
            line_path = TEST_OUTPUT_DIR / f"{base_name}_line_{page_num}.png"
            visualizer.visualize_lines(page_data, output_path=str(line_path))
            visualization_paths["line"][page_num] = str(line_path)
        except Exception as e:
            logging.warning(f"Failed to visualize lines for page {page_num}: {e}")
    
    return visualization_paths


@pytest.mark.parametrize("category", ["simple", "multicolumn", pytest.param("tables", marks=pytest.mark.xfail)])
def test_document_visualization(category: str, request):
    """
    Test document parsing visualization with different sample types.
    
    This test:
    1. Processes a sample PDF file
    2. Generates visualizations at different granularity levels
    3. Creates an HTML report with the visualizations
    4. Integrates with pytest-html reporting
    
    Args:
        category: Sample type category (simple, multicolumn, tables)
        request: pytest request object for report integration
    """
    if not DOCUMENT_PROCESSING_AVAILABLE:
        pytest.skip("DocumentProcessingService not available")
    
    # Get sample PDF files matching the category
    sample_pdfs = get_sample_pdfs(category)
    assert len(sample_pdfs) > 0, f"No sample PDFs found for category: {category}"
    
    # Use the first matching sample
    pdf_path = sample_pdfs[0]
    logging.info(f"Testing document visualization with sample: {pdf_path}")
    
    # Clean previous test outputs
    clean_previous_outputs(pdf_path)
    
    # Initialize document processing service
    service = DocumentProcessingService(enable_ocr=True)
    
    # Process the document
    try:
        doc_data = service.process_document(str(pdf_path))
        assert doc_data is not None, "Document processing returned None"
        assert "pages" in doc_data, "Document has no pages"
    except Exception as e:
        pytest.fail(f"Document processing failed: {e}")
    
    # Generate visualizations
    visualization_paths = visualize_document(pdf_path, doc_data)
    
    # Generate report
    report_path = generate_visualization_report(
        pdf_path=pdf_path,
        papermage_doc=doc_data,
        visualization_paths=visualization_paths
    )
    
    # Verify report was generated
    if report_path:
        assert os.path.exists(report_path), f"Report not found at {report_path}"
        logging.info(f"Generated visualization report: {report_path}")
        
        # Copy report assets to pytest-html directory
        copy_report_assets_to_pytest_html(report_path, visualization_paths)
        
        # Attach report to pytest result
        attach_report_to_pytest(report_path, request)
    
    # Verify visualizations were generated
    for level_type, pages in visualization_paths.items():
        assert len(pages) > 0, f"No {level_type} visualizations generated"
        for page_num, path in pages.items():
            assert os.path.exists(path), f"{level_type} visualization for page {page_num} not found"


if __name__ == "__main__":
    # Enable running this test directly
    logging.basicConfig(level=logging.INFO)
    import sys
    
    if len(sys.argv) > 1:
        category = sys.argv[1]
    else:
        category = "simple"
    
    # Create a mock request object
    class MockRequest:
        class MockNode:
            user_properties = []
        node = MockNode()
    
    # Run the test
    test_document_visualization(category, MockRequest()) 