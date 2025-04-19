#!/usr/bin/env python
"""
Docling-Style Visualization Tool

This script provides visualization similar to the Docling GitHub example,
showing text extraction at different granularity levels (char, word, line).

Examples:
    # Visualize a PDF file at word level
    python -m papermage_docling.visualizers.docling_visual --input sample.pdf --cell-unit word

    # Visualize with RTL support and save output
    python -m papermage_docling.visualizers.docling_visual --input rtl_doc.pdf --cell-unit line --output ./output
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Union, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Check if required packages are available
try:
    from PIL import Image, ImageDraw, ImageFont
    import matplotlib.pyplot as plt
    import numpy as np
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    logger.error("Visualization libraries not available. Please install: matplotlib, numpy, pillow")

# Check if Docling is available
try:
    from docling.document_converter import DocumentConverter
    from docling.backend.docling_parse_v4_backend import TextCellUnit
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    logger.warning("Docling not available. Will use PaperMage-only visualization.")
    # Define fallback TextCellUnit (just for type hints)
    class TextCellUnit:
        CHAR = "char"
        WORD = "word"
        LINE = "line"

# Import PaperMage converter
try:
    from papermage_docling.converter import convert_document
except ImportError:
    logger.error("papermage_docling.converter not found")
    sys.exit(1)


class DoclingVisualizer:
    """
    Visualizer for document parsing at different levels of granularity (char, word, line).
    """
    
    def __init__(self, output_dir: Optional[Union[str, Path]] = None, interactive: bool = False):
        """
        Initialize the visualizer.
        
        Args:
            output_dir: Directory to save visualizations
            interactive: Whether to display visualizations interactively
        """
        if not VISUALIZATION_AVAILABLE:
            raise ImportError("Visualization libraries not available")
        
        self.output_dir = Path(output_dir) if output_dir else None
        self.interactive = interactive
        
        # Create output directory if needed
        if self.output_dir and not self.output_dir.exists():
            os.makedirs(self.output_dir)
            logger.info(f"Created output directory: {self.output_dir}")
    
    def visualize_pdf(
        self, 
        pdf_path: Union[str, Path], 
        cell_unit: str = "word",
        pages: Optional[List[int]] = None
    ) -> List[Path]:
        """
        Visualize a PDF document with text extraction at specified granularity.
        
        Args:
            pdf_path: Path to the PDF file
            cell_unit: Cell unit for visualization (char, word, line)
            pages: List of pages to visualize (None for all)
            
        Returns:
            List of paths to generated visualization files
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Map text cell unit string to enum
        cell_unit_map = {
            "char": TextCellUnit.CHAR,
            "word": TextCellUnit.WORD,
            "line": TextCellUnit.LINE
        }
        
        if cell_unit not in cell_unit_map:
            raise ValueError(f"Invalid cell_unit: {cell_unit}. Must be one of: {', '.join(cell_unit_map.keys())}")
        
        if DOCLING_AVAILABLE:
            # Use Docling for visualization
            return self._visualize_with_docling(pdf_path, cell_unit_map[cell_unit], pages)
        else:
            # Use PaperMage for visualization
            return self._visualize_with_papermage(pdf_path, cell_unit, pages)
    
    def _visualize_with_docling(
        self,
        pdf_path: Path,
        cell_unit: TextCellUnit,
        pages: Optional[List[int]] = None
    ) -> List[Path]:
        """
        Visualize PDF using native Docling functionality.
        
        Args:
            pdf_path: Path to the PDF file
            cell_unit: TextCellUnit enum value
            pages: List of pages to visualize (None for all)
            
        Returns:
            List of paths to generated visualization files
        """
        # Initialize Docling document converter
        logger.info(f"Loading PDF with Docling: {pdf_path}")
        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))
        doc = result.document
        
        # Get pages to visualize
        if pages is None:
            pages = list(range(1, len(doc.pages) + 1))
        
        # Visualize each page
        output_paths = []
        for page_num in pages:
            if page_num > len(doc.pages):
                logger.warning(f"Page {page_num} out of range. Document has {len(doc.pages)} pages.")
                continue
            
            # Get PDF page and render as image
            pdf_page = doc._pdf_document.get_page(page_num)
            
            # Create a figure with original and cell-level visualization
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 10))
            
            # Original PDF
            img_orig = pdf_page.render_as_image()
            ax1.imshow(np.array(img_orig))
            ax1.set_title(f"Original PDF - Page {page_num}")
            ax1.axis('off')
            
            # Cell-level visualization
            img_cells = pdf_page.render_as_image(cell_unit=cell_unit, draw_cells_bbox=True)
            ax2.imshow(np.array(img_cells))
            ax2.set_title(f"Docling - {cell_unit.name} Level")
            ax2.axis('off')
            
            # Add figure title
            fig.suptitle(f"Document Parsing: {pdf_path.name} - Page {page_num}", fontsize=16)
            
            # Save or show the figure
            if self.output_dir:
                output_path = self.output_dir / f"{pdf_path.stem}_page{page_num}_{cell_unit.name.lower()}.png"
                plt.savefig(output_path, dpi=150, bbox_inches='tight')
                output_paths.append(output_path)
                logger.info(f"Saved visualization to {output_path}")
            
            if self.interactive:
                plt.show()
            else:
                plt.close(fig)
        
        return output_paths
    
    def _visualize_with_papermage(
        self,
        pdf_path: Path,
        cell_unit: str,
        pages: Optional[List[int]] = None
    ) -> List[Path]:
        """
        Visualize PDF using PaperMage-based visualization when Docling is not available.
        
        Args:
            pdf_path: Path to the PDF file
            cell_unit: Cell unit string ('char', 'word', 'line')
            pages: List of pages to visualize (None for all)
            
        Returns:
            List of paths to generated visualization files
        """
        # Convert the document with PaperMage-Docling
        logger.info(f"Converting document with PaperMage-Docling: {pdf_path}")
        try:
            pm_doc = convert_document(pdf_path)
        except Exception as e:
            logger.error(f"Failed to convert document with PaperMage-Docling: {e}")
            return []
        
        # Get pages to visualize
        if pages is None:
            pages = list(range(1, len(pm_doc.get("pages", [])) + 1))
        
        # Visualize each page
        output_paths = []
        for page_idx in range(len(pm_doc.get("pages", []))):
            page_num = page_idx + 1
            if page_num not in pages:
                continue
            
            # Get page data
            page = pm_doc["pages"][page_idx]
            
            # Set up the plot
            fig, ax = plt.subplots(figsize=(12, 16))
            fig.suptitle(f"Document Parsing: {pdf_path.name} - Page {page_num} ({cell_unit} level)", fontsize=16)
            
            # Set page dimensions
            width = page.get("width", 612)  # Default letter width
            height = page.get("height", 792)  # Default letter height
            
            # Set axis limits
            ax.set_xlim(0, width)
            ax.set_ylim(0, height)
            ax.invert_yaxis()  # Origin at top-left
            
            # Draw different elements based on the requested cell unit
            if cell_unit == "word":
                # Draw word boxes
                for word in page.get("words", []):
                    if "box" in word:
                        box = word["box"]
                        rect = plt.Rectangle(
                            (box["x0"], box["y0"]), 
                            box["x1"] - box["x0"], 
                            box["y1"] - box["y0"],
                            linewidth=1, 
                            edgecolor="blue", 
                            facecolor='none'
                        )
                        ax.add_patch(rect)
                        
                        # Add text
                        if "text" in word:
                            ax.text(
                                box["x0"], box["y0"] - 2,
                                word["text"],
                                fontsize=8,
                                color="blue",
                                verticalalignment='bottom'
                            )
            
            elif cell_unit == "line":
                # For line level, group words by y-position (approximate lines)
                words = page.get("words", [])
                if words:
                    # Group words into lines based on y-position
                    line_groups = {}
                    for word in words:
                        if "box" not in word:
                            continue
                        
                        box = word["box"]
                        y_center = (box["y0"] + box["y1"]) / 2
                        # Round to nearest 5 pixels to group words in the same line
                        line_key = round(y_center / 5) * 5
                        
                        if line_key not in line_groups:
                            line_groups[line_key] = []
                        line_groups[line_key].append(word)
                    
                    # Draw line boxes
                    for line_key, line_words in line_groups.items():
                        if not line_words:
                            continue
                            
                        # Calculate bounding box for the line
                        min_x = min(word["box"]["x0"] for word in line_words)
                        max_x = max(word["box"]["x1"] for word in line_words)
                        min_y = min(word["box"]["y0"] for word in line_words)
                        max_y = max(word["box"]["y1"] for word in line_words)
                        
                        # Draw line box
                        rect = plt.Rectangle(
                            (min_x, min_y), 
                            max_x - min_x, 
                            max_y - min_y,
                            linewidth=1, 
                            edgecolor="green", 
                            facecolor='none'
                        )
                        ax.add_patch(rect)
                        
                        # Add text
                        line_text = " ".join(word.get("text", "") for word in line_words)
                        ax.text(
                            min_x, min_y - 5,
                            line_text[:50] + ("..." if len(line_text) > 50 else ""),
                            fontsize=8,
                            color="green",
                            verticalalignment='bottom'
                        )
            
            else:  # char level - just show word boxes with smaller granularity
                for word in page.get("words", []):
                    if "box" in word and "text" in word:
                        box = word["box"]
                        text = word["text"]
                        
                        # Approximate character boxes by dividing word box width
                        if not text:
                            continue
                            
                        char_width = (box["x1"] - box["x0"]) / len(text)
                        for i, char in enumerate(text):
                            char_x0 = box["x0"] + i * char_width
                            char_x1 = char_x0 + char_width
                            
                            # Draw character box
                            rect = plt.Rectangle(
                                (char_x0, box["y0"]), 
                                char_width, 
                                box["y1"] - box["y0"],
                                linewidth=0.5, 
                                edgecolor="red", 
                                facecolor='none'
                            )
                            ax.add_patch(rect)
            
            # Draw tables and figures if they exist
            for entity in page.get("entities", []):
                if "box" in entity and "id" in entity:
                    box = entity["box"]
                    entity_id = entity["id"]
                    
                    # Determine color based on entity type
                    if entity_id.startswith("table"):
                        color = "purple"
                    elif entity_id.startswith("figure"):
                        color = "orange"
                    else:
                        color = "gray"
                    
                    # Draw entity box
                    rect = plt.Rectangle(
                        (box["x0"], box["y0"]), 
                        box["x1"] - box["x0"], 
                        box["y1"] - box["y0"],
                        linewidth=2, 
                        edgecolor=color, 
                        facecolor='none', 
                        alpha=0.7
                    )
                    ax.add_patch(rect)
                    
                    # Add entity label
                    ax.text(
                        box["x0"], box["y0"] - 10,
                        entity_id,
                        fontsize=10,
                        color=color,
                        weight='bold',
                        verticalalignment='bottom'
                    )
            
            # Add legend
            legend_elements = []
            if cell_unit == "word":
                legend_elements.append(plt.Rectangle((0, 0), 1, 1, edgecolor="blue", facecolor='none', label='Words'))
            elif cell_unit == "line":
                legend_elements.append(plt.Rectangle((0, 0), 1, 1, edgecolor="green", facecolor='none', label='Lines'))
            else:  # char
                legend_elements.append(plt.Rectangle((0, 0), 1, 1, edgecolor="red", facecolor='none', label='Characters'))
            
            # Add entity types to legend
            legend_elements.append(plt.Rectangle((0, 0), 1, 1, edgecolor="purple", facecolor='none', label='Tables'))
            legend_elements.append(plt.Rectangle((0, 0), 1, 1, edgecolor="orange", facecolor='none', label='Figures'))
            
            ax.legend(handles=legend_elements, loc='upper right')
            
            # Set aspect ratio
            ax.set_aspect('equal')
            
            # Save or show the figure
            if self.output_dir:
                output_path = self.output_dir / f"{pdf_path.stem}_page{page_num}_{cell_unit}.png"
                plt.savefig(output_path, dpi=150, bbox_inches='tight')
                output_paths.append(output_path)
                logger.info(f"Saved visualization to {output_path}")
            
            if self.interactive:
                plt.show()
            else:
                plt.close(fig)
        
        return output_paths


def main():
    """
    Main function to run the visualization tool.
    """
    # Check prerequisites
    if not VISUALIZATION_AVAILABLE:
        logger.error("Visualization libraries not available. Please install: matplotlib, numpy, pillow")
        return 1
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Visualize PDF document parsing at different text levels")
    
    parser.add_argument(
        "-i", "--input",
        type=str,
        required=True,
        help="Path to the PDF file to visualize"
    )
    
    parser.add_argument(
        "-c", "--cell-unit",
        type=str,
        choices=["char", "word", "line"],
        default="word",
        help="Text cell unit level for visualization"
    )
    
    parser.add_argument(
        "-p", "--pages",
        type=str,
        help="Pages to visualize (comma-separated, e.g., '1,2,3')"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Directory to save visualizations"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Display visualizations interactively"
    )
    
    args = parser.parse_args()
    
    # Parse pages if provided
    pages = None
    if args.pages:
        try:
            pages = [int(p.strip()) for p in args.pages.split(",")]
        except ValueError:
            logger.error("Invalid page format. Use comma-separated integers (e.g., '1,2,3')")
            return 1
    
    # Initialize visualizer
    visualizer = DoclingVisualizer(
        output_dir=args.output,
        interactive=args.interactive
    )
    
    # Run visualization
    try:
        output_paths = visualizer.visualize_pdf(
            pdf_path=args.input,
            cell_unit=args.cell_unit,
            pages=pages
        )
        
        if output_paths:
            logger.info(f"Generated {len(output_paths)} visualizations.")
            for path in output_paths:
                logger.info(f"- {path}")
        else:
            logger.warning("No visualizations were generated.")
        
        return 0
    except Exception as e:
        logger.error(f"Visualization failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 