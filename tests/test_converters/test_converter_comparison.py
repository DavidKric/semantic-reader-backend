"""
Test module for comparing document_converter against document_parser using v4 backend.

This module provides comprehensive testing that compares:
1. The PaperMage-Docling document_converter implementation
2. The original document_parser implementation using Docling's v4 backend

It includes visualization capabilities to inspect and compare the results visually.
"""

import os
import json
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import pytest
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from matplotlib.gridspec import GridSpec

# Import our implementations
from papermage_docling.converter import convert_document, docling_to_papermage

# Try to import Docling for direct comparison
try:
    from docling.document_converter import DocumentConverter
    from docling.backend.docling_parse_v4_backend import TextCellUnit
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

# Skip tests if Docling dependencies are not available
pytestmark = pytest.mark.skipif(not DOCLING_AVAILABLE, reason="Docling dependencies not available")

# Define test directories
TEST_DIR = Path(__file__).parent.parent
TEST_DATA_DIR = TEST_DIR / "data"
TEST_FIXTURES_DIR = TEST_DATA_DIR / "fixtures"
TEST_SAMPLES_DIR = TEST_FIXTURES_DIR / "samples"
TEST_TEMP_DIR = TEST_DATA_DIR / "temp"


class ConverterComparisonVisualizer:
    """
    Visualizer class for comparing document conversion results.
    
    This visualizer generates side-by-side visualizations of document conversions
    from both PaperMage-Docling converter and direct Docling parsing.
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize the visualizer."""
        self.output_dir = output_dir or TEST_TEMP_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def visualize_comparison(
        self,
        pdf_path: Path,
        papermage_result: Dict[str, Any],
        docling_doc: Any,
        page_num: int = 1,
        show_interactive: bool = False
    ) -> Path:
        """
        Create a visual comparison between papermage and docling parsing results.
        
        Args:
            pdf_path: Path to the original PDF file
            papermage_result: Result from papermage_docling converter
            docling_doc: DoclingDocument from direct Docling conversion
            page_num: Page number to visualize (1-indexed)
            show_interactive: Whether to show the visualization interactively
            
        Returns:
            Path to the saved visualization image file
        """
        # Create a figure with 2 rows and 3 columns
        fig = plt.figure(figsize=(18, 12))
        gs = GridSpec(2, 3, figure=fig, height_ratios=[1, 1])
        
        # Original PDF page
        ax_orig = fig.add_subplot(gs[0, 0])
        # Docling character-level visualization
        ax_docling_char = fig.add_subplot(gs[0, 1])
        # Docling word-level visualization
        ax_docling_word = fig.add_subplot(gs[0, 2])
        # Docling line-level visualization
        ax_docling_line = fig.add_subplot(gs[1, 0])
        # PaperMage visualization
        ax_papermage = fig.add_subplot(gs[1, 1])
        # Stats comparison
        ax_stats = fig.add_subplot(gs[1, 2])
        
        # Get PDF page
        pdf_page = docling_doc._pdf_document.get_page(page_num)
        
        # Original PDF rendering
        img_orig = pdf_page.render_as_image()
        ax_orig.imshow(np.array(img_orig))
        ax_orig.set_title(f"Original PDF - Page {page_num}")
        ax_orig.axis('off')
        
        # Docling character-level visualization
        img_char = pdf_page.render_as_image(cell_unit=TextCellUnit.CHAR, draw_cells_bbox=True)
        ax_docling_char.imshow(np.array(img_char))
        ax_docling_char.set_title("Docling - Character Level")
        ax_docling_char.axis('off')
        
        # Docling word-level visualization
        img_word = pdf_page.render_as_image(cell_unit=TextCellUnit.WORD, draw_cells_bbox=True)
        ax_docling_word.imshow(np.array(img_word))
        ax_docling_word.set_title("Docling - Word Level")
        ax_docling_word.axis('off')
        
        # Docling line-level visualization
        img_line = pdf_page.render_as_image(cell_unit=TextCellUnit.LINE, draw_cells_bbox=True)
        ax_docling_line.imshow(np.array(img_line))
        ax_docling_line.set_title("Docling - Line Level")
        ax_docling_line.axis('off')
        
        # PaperMage visualization (render original image with boxes from PaperMage result)
        papermage_overlay = self._draw_papermage_overlay(
            img_orig.copy(), 
            papermage_result, 
            page_idx=page_num-1
        )
        ax_papermage.imshow(np.array(papermage_overlay))
        ax_papermage.set_title("PaperMage Overlay")
        ax_papermage.axis('off')
        
        # Statistics comparison
        self._plot_stats_comparison(
            ax_stats, 
            papermage_result, 
            docling_doc, 
            page_num
        )
        
        # Adjust layout and save
        plt.tight_layout()
        output_path = self.output_dir / f"{pdf_path.stem}_page{page_num}_comparison.png"
        plt.savefig(output_path, dpi=150)
        
        if show_interactive:
            plt.show()
        
        plt.close(fig)
        return output_path
    
    def _draw_papermage_overlay(
        self, 
        base_img: Image.Image, 
        papermage_result: Dict[str, Any], 
        page_idx: int
    ) -> Image.Image:
        """
        Draw PaperMage entities as overlay boxes on the base image.
        
        Args:
            base_img: Base PIL Image
            papermage_result: PaperMage conversion result
            page_idx: Page index (0-indexed)
            
        Returns:
            PIL Image with overlaid boxes
        """
        draw = ImageDraw.Draw(base_img)
        
        # Get page data
        if page_idx >= len(papermage_result.get("pages", [])):
            return base_img
        
        page = papermage_result["pages"][page_idx]
        
        # Draw word boxes
        for word in page.get("words", []):
            if "box" in word:
                box = word["box"]
                # Draw green box for words
                draw.rectangle(
                    [(box["x0"], box["y0"]), (box["x1"], box["y1"])],
                    outline="green",
                    width=1
                )
        
        # Draw entity boxes (tables, figures)
        for entity in page.get("entities", []):
            if "box" in entity:
                box = entity["box"]
                # Determine color based on entity type
                if "id" in entity:
                    if entity["id"].startswith("table"):
                        color = "blue"  # Blue for tables
                    elif entity["id"].startswith("figure"):
                        color = "red"   # Red for figures
                    else:
                        color = "purple"  # Purple for other entities
                        
                    # Draw thicker box for entities
                    draw.rectangle(
                        [(box["x0"], box["y0"]), (box["x1"], box["y1"])],
                        outline=color,
                        width=2
                    )
        
        return base_img
    
    def _plot_stats_comparison(
        self, 
        ax: plt.Axes,
        papermage_result: Dict[str, Any],
        docling_doc: Any,
        page_num: int
    ):
        """
        Plot statistics comparing Docling and PaperMage results.
        
        Args:
            ax: Matplotlib axes to plot on
            papermage_result: PaperMage conversion result
            docling_doc: DoclingDocument from Docling
            page_num: Page number (1-indexed)
        """
        ax.axis('off')
        ax.set_title("Stats Comparison")
        
        # Get PaperMage page stats
        if page_num-1 < len(papermage_result.get("pages", [])):
            pm_page = papermage_result["pages"][page_num-1]
            pm_word_count = len(pm_page.get("words", []))
            pm_table_count = sum(1 for e in pm_page.get("entities", []) if "id" in e and e["id"].startswith("table"))
            pm_figure_count = sum(1 for e in pm_page.get("entities", []) if "id" in e and e["id"].startswith("figure"))
        else:
            pm_word_count = pm_table_count = pm_figure_count = 0
        
        # Get Docling page stats
        docling_page = docling_doc.pages[page_num-1] if page_num-1 < len(docling_doc.pages) else None
        
        if docling_page:
            dl_word_count = len(docling_page.words) if hasattr(docling_page, "words") else 0
            dl_table_count = len(docling_page.tables) if hasattr(docling_page, "tables") else 0
            dl_figure_count = len(docling_page.figures) if hasattr(docling_page, "figures") else 0
        else:
            dl_word_count = dl_table_count = dl_figure_count = 0
        
        # Stats text
        stats_text = (
            f"PaperMage Converter:\n"
            f"- Words: {pm_word_count}\n"
            f"- Tables: {pm_table_count}\n"
            f"- Figures: {pm_figure_count}\n\n"
            f"Docling Parser:\n"
            f"- Words: {dl_word_count}\n"
            f"- Tables: {dl_table_count}\n"
            f"- Figures: {dl_figure_count}\n"
        )
        
        ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, 
                fontsize=12, verticalalignment='top', family='monospace')


def test_converter_comparison():
    """
    Test and visualize the comparison between PaperMage-Docling converter and direct Docling document parsing.
    
    This test:
    1. Finds a sample PDF to test with
    2. Processes it with both PaperMage-Docling converter and direct Docling
    3. Creates visualizations showing the differences
    4. Verifies that core structures are correctly captured in both approaches
    """
    # Find a sample PDF to test
    sample_categories = ["simple", "complex", "multi_column"]
    sample_pdf = None
    
    for category in sample_categories:
        category_dir = TEST_SAMPLES_DIR / category
        if category_dir.exists():
            pdf_files = list(category_dir.glob("*.pdf"))
            if pdf_files:
                sample_pdf = pdf_files[0]
                break
    
    if not sample_pdf:
        pytest.skip("No sample PDF files found for testing")
    
    print(f"Testing with sample PDF: {sample_pdf}")
    
    # Initialize visualizer
    visualizer = ConverterComparisonVisualizer(output_dir=TEST_TEMP_DIR)
    
    # Conversion options (same for both approaches)
    options = {
        "detect_tables": True,
        "detect_figures": True,
        "enable_ocr": False
    }
    
    # 1. Process with PaperMage-Docling converter
    pm_start_time = time.time()
    papermage_result = convert_document(str(sample_pdf), options)
    pm_elapsed = time.time() - pm_start_time
    
    # 2. Process with direct Docling
    docling_start_time = time.time()
    converter = DocumentConverter(
        tables=options.get("detect_tables", True),
        figures=options.get("detect_figures", True),
        ocr=options.get("enable_ocr", False)
    )
    docling_result = converter.convert(str(sample_pdf))
    docling_elapsed = time.time() - docling_start_time
    
    # Get the DoclingDocument for visualization
    docling_doc = docling_result.document
    
    # Generate visualization for the first page
    output_path = visualizer.visualize_comparison(
        pdf_path=sample_pdf,
        papermage_result=papermage_result,
        docling_doc=docling_doc,
        page_num=1,
        show_interactive=False
    )
    
    # Print timing information
    print(f"\nProcessing times:")
    print(f"- PaperMage-Docling converter: {pm_elapsed:.2f} seconds")
    print(f"- Direct Docling processing: {docling_elapsed:.2f} seconds")
    print(f"- Visualization saved to: {output_path}")
    
    # Verify some key structures are captured
    # 1. Page dimensions
    if papermage_result.get("pages") and len(papermage_result["pages"]) > 0:
        pm_page = papermage_result["pages"][0]
        dl_page = docling_doc.pages[0]
        
        assert pm_page.get("width") > 0, "Page width should be positive"
        assert pm_page.get("height") > 0, "Page height should be positive"
        
        # Basic dimensions should match (might be scaled slightly)
        assert abs(pm_page.get("width") - dl_page.width) / dl_page.width < 0.1, "Page width should be similar"
        assert abs(pm_page.get("height") - dl_page.height) / dl_page.height < 0.1, "Page height should be similar"
    
    # 2. Words should be detected 
    if papermage_result.get("pages") and len(papermage_result["pages"]) > 0:
        pm_page = papermage_result["pages"][0]
        assert "words" in pm_page, "Words should be present in PaperMage result"
        assert len(pm_page["words"]) > 0, "Words should be detected in PaperMage result"
    
    # 3. Check that the language was properly detected
    assert "metadata" in papermage_result, "Metadata should be present in PaperMage result"
    assert "language" in papermage_result["metadata"], "Language should be detected in PaperMage result"
    
    # Return visualization path for potential further use
    return output_path


def test_multipage_converter_comparison():
    """
    Test the comparison on a multi-page document, checking consistency across pages.
    """
    # Find a multi-page PDF to test
    multi_page_pdf = None
    
    for category in ["complex", "multi_column"]:
        category_dir = TEST_SAMPLES_DIR / category
        if category_dir.exists():
            for pdf_file in category_dir.glob("*.pdf"):
                # Check if it's a multi-page PDF
                try:
                    converter = DocumentConverter()
                    result = converter.convert(str(pdf_file))
                    if len(result.document.pages) > 1:
                        multi_page_pdf = pdf_file
                        break
                except Exception:
                    continue
        if multi_page_pdf:
            break
    
    if not multi_page_pdf:
        pytest.skip("No multi-page PDF files found for testing")
    
    print(f"Testing with multi-page PDF: {multi_page_pdf}")
    
    # Initialize visualizer
    visualizer = ConverterComparisonVisualizer(output_dir=TEST_TEMP_DIR)
    
    # Conversion options
    options = {
        "detect_tables": True,
        "detect_figures": True,
        "enable_ocr": False
    }
    
    # Process with both converters
    papermage_result = convert_document(str(multi_page_pdf), options)
    
    converter = DocumentConverter(
        tables=options.get("detect_tables", True),
        figures=options.get("detect_figures", True),
        ocr=options.get("enable_ocr", False)
    )
    docling_result = converter.convert(str(multi_page_pdf))
    docling_doc = docling_result.document
    
    # Test all pages for consistency
    num_pages = min(len(papermage_result.get("pages", [])), len(docling_doc.pages))
    
    # Create visualizations for all pages
    for page_num in range(1, num_pages + 1):
        output_path = visualizer.visualize_comparison(
            pdf_path=multi_page_pdf,
            papermage_result=papermage_result,
            docling_doc=docling_doc,
            page_num=page_num,
            show_interactive=False
        )
        
        print(f"Generated visualization for page {page_num}: {output_path}")
    
    # Verify page count
    assert len(papermage_result.get("pages", [])) == len(docling_doc.pages), \
        "Page count should match between PaperMage and Docling"
    
    # Return number of pages processed
    return num_pages 