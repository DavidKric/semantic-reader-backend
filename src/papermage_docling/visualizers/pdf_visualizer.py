"""
PDF document visualization tools for papermage_docling.

This module provides functionality to visualize PDF documents processed by
Docling, rendering pages with visualization of various text units
and their bounding boxes.
"""

import argparse
import logging
import os
from pathlib import Path
from typing import Literal, Optional, Union

# Import Docling document structures
try:
    from docling.backend.docling_parse_v4_backend import SegmentedPdfPage, TextCellUnit
    from docling.datamodel.document import DoclingDocument
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    logging.warning("Docling dependencies not found. Visualization functionality will be limited.")
    DOCLING_AVAILABLE = False
    # Define stub classes for type hints
    class SegmentedPdfPage:
        pass
    
    class TextCellUnit:
        CHAR = "char"
        WORD = "word"
        LINE = "line"
    
    class DoclingDocument:
        pass

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class PdfVisualizer:
    """
    Visualize PDF documents processed by Docling.
    
    This class provides methods to visualize PDF documents at different granularity
    levels (character, word, line), with options to highlight text and bounding boxes.
    """
    
    def __init__(
        self,
        log_level: str = "info",
        display_text: bool = True,
        interactive: bool = False,
        output_dir: Optional[Path] = None,
        page_boundary: str = "crop_box"
    ):
        """
        Initialize the PDF visualizer.
        
        Args:
            log_level: Logging level ('info', 'warning', 'error', 'fatal')
            display_text: Whether to display text in visualizations
            interactive: Whether to show visualizations interactively
            output_dir: Directory to save visualization images
            page_boundary: Page boundary type ('crop_box', 'media_box')
        """
        self.log_level = log_level
        self.display_text = display_text
        self.interactive = interactive
        self.output_dir = output_dir
        self.page_boundary = page_boundary
        
        # Set up logging
        numeric_level = getattr(logging, self.log_level.upper(), logging.ERROR)
        logging.getLogger().setLevel(numeric_level)
        
        logger.info(f"Initialized PdfVisualizer (display_text: {display_text}, "
                   f"interactive: {interactive}, output_dir: {output_dir})")
    
    def visualize_pdf(
        self,
        pdf_path: Union[str, Path],
        page_num: int = -1,
        category: Literal["all", "char", "word", "line"] = "all",
        parser_kwargs: Optional[dict] = None
    ):
        """
        Visualize a PDF document.
        
        Args:
            pdf_path: Path to the PDF file
            page_num: Page number to visualize (-1 for all pages)
            category: Text unit category to visualize ('all', 'char', 'word', 'line')
            parser_kwargs: Additional keyword arguments for Docling configuration
            
        Returns:
            None
        """
        if not DOCLING_AVAILABLE:
            logger.error("Docling is not available. Cannot visualize PDF.")
            return
            
        logger.info(f"Visualizing PDF: {pdf_path} (page: {page_num}, category: {category})")
        
        # Initialize Docling converter with parser_kwargs
        parser_kwargs = parser_kwargs or {}
        
        # Configure converter arguments
        converter_args = {
            "tables": parser_kwargs.get("detect_tables", True),
            "figures": parser_kwargs.get("detect_figures", True),
            "metadata": True,
            "ocr": parser_kwargs.get("enable_ocr", False),
            "parser": "doclingparse_v4",  # Use DoclingParse v4
            "rtl_enabled": parser_kwargs.get("detect_rtl", True),
        }
        
        # Add OCR language if provided
        if "ocr_language" in parser_kwargs:
            converter_args["ocr_language"] = parser_kwargs["ocr_language"]
        
        # Create converter
        converter = DocumentConverter(**converter_args)
        
        # Load PDF document
        result = converter.convert(str(pdf_path))
        
        # Get the DoclingDocument
        docling_doc = result.document
        
        # Get the PDF document from Docling's result for visualization
        # This uses internal document storage for visualization purposes
        pdf_doc = docling_doc._pdf_document
        
        # Determine pages to visualize
        page_nos = [page_num]
        if page_num == -1:
            page_nos = list(range(1, len(pdf_doc.pages) + 1))
        
        # Create output directory if needed
        if self.output_dir and not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"Created output directory: {self.output_dir}")
        
        # Visualize each page
        for page_no in page_nos:
            logger.info(f"Visualizing page {page_no} of {pdf_path}")
            
            # Get the page
            pdf_page = pdf_doc.get_page(page_no)
            
            # Visualize at different levels of granularity
            self._visualize_page(
                pdf_page=pdf_page,
                page_no=page_no,
                category=category,
                pdf_path=pdf_path
            )
    
    def _visualize_page(
        self,
        pdf_page: SegmentedPdfPage,
        page_no: int,
        category: str,
        pdf_path: Union[str, Path]
    ):
        """
        Visualize a single PDF page at different granularity levels.
        
        Args:
            pdf_page: The PDF page to visualize
            page_no: Page number
            category: Text unit category ('all', 'char', 'word', 'line')
            pdf_path: Path to the PDF file (for naming output files)
            
        Returns:
            None
        """
        pdf_basename = os.path.basename(str(pdf_path))
        
        # Character-level visualization
        if category in ["all", "char"]:
            logger.info(f"Visualizing characters on page {page_no}")
            self._visualize_cell_unit(
                pdf_page=pdf_page,
                cell_unit=TextCellUnit.CHAR,
                page_no=page_no,
                pdf_basename=pdf_basename,
                unit_name="char"
            )
        
        # Word-level visualization
        if category in ["all", "word"]:
            logger.info(f"Visualizing words on page {page_no}")
            self._visualize_cell_unit(
                pdf_page=pdf_page,
                cell_unit=TextCellUnit.WORD,
                page_no=page_no,
                pdf_basename=pdf_basename,
                unit_name="word"
            )
        
        # Line-level visualization
        if category in ["all", "line"]:
            logger.info(f"Visualizing lines on page {page_no}")
            self._visualize_cell_unit(
                pdf_page=pdf_page,
                cell_unit=TextCellUnit.LINE,
                page_no=page_no,
                pdf_basename=pdf_basename,
                unit_name="line"
            )
    
    def _visualize_cell_unit(
        self,
        pdf_page: SegmentedPdfPage,
        cell_unit: TextCellUnit,
        page_no: int,
        pdf_basename: str,
        unit_name: str
    ):
        """
        Visualize a specific text cell unit on a page.
        
        Args:
            pdf_page: The PDF page to visualize
            cell_unit: The text cell unit type (CHAR, WORD, LINE)
            page_no: Page number
            pdf_basename: Base name of the PDF file
            unit_name: Name of the unit for output file naming
            
        Returns:
            None
        """
        try:
            # Render the page with bounding boxes
            img = pdf_page.render_as_image(
                cell_unit=cell_unit,
                draw_cells_bbox=not self.display_text,
                draw_cells_text=self.display_text,
            )
            
            # Save to file if output directory is specified
            if self.output_dir:
                output_path = os.path.join(
                    self.output_dir,
                    f"{pdf_basename}.page_{page_no}.{unit_name}.png"
                )
                img.save(output_path)
                logger.info(f"Saved visualization to {output_path}")
            
            # Show interactively if enabled
            if self.interactive:
                img.show()
            
            # Log text if needed
            if logger.level <= logging.INFO:
                try:
                    lines = pdf_page.export_to_textlines(
                        cell_unit=cell_unit,
                        add_fontkey=True,
                        add_fontname=False,
                    )
                    logger.info(f"Text {unit_name}s (page {page_no}):")
                    for i, line in enumerate(lines[:10]):  # Only show first 10 lines to avoid flooding logs
                        logger.info(f"  {i+1}: {line}")
                    if len(lines) > 10:
                        logger.info(f"  ... and {len(lines) - 10} more lines")
                except Exception as e:
                    logger.warning(f"Failed to export text lines: {e}")
            
        except Exception as e:
            logger.error(f"Failed to visualize {unit_name}s on page {page_no}: {e}")


def parse_args():
    """Parse command-line arguments for the PDF visualization tool."""
    parser = argparse.ArgumentParser(description="Visualize a PDF document.")
    
    # PDF path
    parser.add_argument(
        "-i", "--input-pdf", 
        type=str, 
        required=True,
        help="Path to the PDF file"
    )
    
    # Log level
    parser.add_argument(
        "-l", "--log-level",
        type=str,
        choices=["info", "warning", "error", "fatal"],
        default="error",
        help="Log level [info, warning, error, fatal]"
    )
    
    # Cell unit category
    parser.add_argument(
        "-c", "--category",
        type=str,
        choices=["all", "char", "word", "line"],
        default="all",
        help="Text unit category to visualize [all, char, word, line]"
    )
    
    # Interactive mode
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enable interactive mode to display visualizations"
    )
    
    # Display text option
    parser.add_argument(
        "--display-text",
        action="store_true",
        help="Display text in visualizations instead of bounding boxes"
    )
    
    # Output directory
    parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default=None,
        help="Directory to save visualization images"
    )
    
    # Page number
    parser.add_argument(
        "-p", "--page",
        type=int,
        default=-1,
        help="Page number to visualize (-1 for all pages)"
    )
    
    # Page boundary
    parser.add_argument(
        "-b", "--page-boundary",
        type=str,
        choices=["crop_box", "media_box"],
        default="crop_box",
        help="Page boundary type [crop_box, media_box]"
    )
    
    # OCR options
    parser.add_argument(
        "--enable-ocr",
        action="store_true",
        help="Enable OCR for scanned documents"
    )
    
    parser.add_argument(
        "--ocr-language",
        type=str,
        default="eng",
        help="OCR language code (e.g., 'eng', 'ara')"
    )
    
    # RTL detection
    parser.add_argument(
        "--detect-rtl",
        action="store_true",
        help="Enable right-to-left text detection and processing"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not os.path.exists(args.input_pdf):
        parser.error(f"PDF file does not exist: {args.input_pdf}")
    
    return args


def main():
    """
    Main entry point for the PDF visualization tool.
    
    Can be run from the command line:
    
    python -m papermage_docling.visualizers.pdf_visualizer -i example.pdf -o ./output -c all
    """
    # Parse command-line arguments
    args = parse_args()
    
    # Initialize the visualizer
    visualizer = PdfVisualizer(
        log_level=args.log_level,
        display_text=args.display_text,
        interactive=args.interactive,
        output_dir=args.output_dir,
        page_boundary=args.page_boundary
    )
    
    # Set up parser kwargs
    parser_kwargs = {
        "enable_ocr": args.enable_ocr,
        "ocr_language": args.ocr_language,
        "detect_rtl": args.detect_rtl
    }
    
    # Visualize the PDF
    visualizer.visualize_pdf(
        pdf_path=args.input_pdf,
        page_num=args.page,
        category=args.category,
        parser_kwargs=parser_kwargs
    )


if __name__ == "__main__":
    main() 