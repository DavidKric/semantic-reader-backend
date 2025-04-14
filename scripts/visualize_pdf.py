#!/usr/bin/env python3
"""
PDF Visualization Script for DoclingPdfParser

This script provides visualization capabilities for the DoclingPdfParser,
allowing users to render PDF pages with different visualization options
(character, word, or line level) and save or display the results.
"""

import argparse
import logging
import os
from pathlib import Path
import sys

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import required types from Docling if available
try:
    from docling_core.types.doc.page import TextCellUnit
except ImportError:
    # Define a stub TextCellUnit class if Docling is not available
    class TextCellUnit:
        CHAR = "CHAR"
        WORD = "WORD"
        LINE = "LINE"

# Import our DoclingPdfParser
from src.papermage_docling.parsers import DoclingPdfParser

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Process and visualize a PDF file.")

    # Restrict log-level to specific values
    parser.add_argument(
        "-l",
        "--log-level",
        type=str,
        choices=["info", "warning", "error", "fatal"],
        required=False,
        default="error",
        help="Log level [info, warning, error, fatal]",
    )

    # Restrict page-boundary
    parser.add_argument(
        "-b",
        "--page-boundary",
        type=str,
        choices=["crop_box", "media_box"],
        required=False,
        default="crop_box",
        help="page-boundary [crop_box, media_box]",
    )

    # Text cell visualization category
    parser.add_argument(
        "-c",
        "--category",
        type=str,
        choices=["all", "char", "word", "line"],
        required=False,
        default="all",
        help="category [all, char, word, line]",
    )

    # Add an argument for the path to the PDF file
    parser.add_argument(
        "-i", "--input-pdf", type=str, help="Path to the PDF file", required=True
    )

    # Add an optional boolean argument for interactive mode
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enable interactive mode to display images (default: False)",
    )

    # Add an optional boolean argument for displaying text
    parser.add_argument(
        "--display-text",
        action="store_true",
        help="Display text in visualizations instead of bounding boxes (default: False)",
    )

    # Add an optional boolean argument for logging text
    parser.add_argument(
        "--log-text",
        action="store_true",
        help="Log extracted text to console (default: False)",
    )

    # Add an argument for the output directory
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        required=False,
        default=None,
        help="Path to the output directory (default: None)",
    )

    # Add an argument for specifying a page number
    parser.add_argument(
        "-p",
        "--page",
        type=int,
        required=False,
        default=-1,
        help="Page to be displayed (default: -1 -> all pages)",
    )

    # Add RTL detection option
    parser.add_argument(
        "--rtl",
        action="store_true",
        help="Enable RTL text detection and processing (default: False)",
    )
    
    # Add language detection option
    parser.add_argument(
        "--language-detection",
        action="store_true",
        help="Enable language detection (default: False)",
    )

    # Parse the command-line arguments
    args = parser.parse_args()

    # Check if the PDF file exists
    if not os.path.exists(args.input_pdf):
        parser.error(f"PDF file does not exist: {args.input_pdf}")

    # Check if the output directory exists, create it if not
    if args.output_dir is not None and not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        logging.info(f"Output directory '{args.output_dir}' created.")

    return args


def visualize_pdf(args):
    """
    Visualize PDF pages using DoclingPdfParser.
    
    Args:
        args: Command-line arguments
    """
    # Initialize the parser with the specified options
    parser = DoclingPdfParser(
        loglevel=args.log_level,
        detect_rtl=args.rtl,
        enable_language_detection=args.language_detection
    )
    
    try:
        # Load the PDF document
        pdf_doc = parser.parse(
            args.input_pdf, 
            output_format='docling',
            boundary_type=args.page_boundary,
            lazy=False
        )
        
        # Get total number of pages
        total_pages = pdf_doc.number_of_pages()
        logging.info(f"Document has {total_pages} pages")
        
        # Determine which pages to process
        page_nos = [args.page]
        if args.page == -1:
            page_nos = list(range(1, total_pages + 1))
        
        # Process each selected page
        for page_no in page_nos:
            logging.info(f"Processing {args.input_pdf} on page: {page_no}")
            
            # Load the specific page
            # Our DoclingPdfParser uses a different iteration/access pattern
            # Convert to 0-based indexing for internal use
            page_idx = page_no - 1
            
            # Find the page in the document
            page = None
            for idx, p in pdf_doc.iterate_pages():
                if idx == page_idx:
                    page = p
                    break
            
            if page is None:
                logging.error(f"Page {page_no} not found in document (has {total_pages} pages)")
                continue
            
            # Now we have the correct page, process it based on the selected categories
            try:
                if args.category in ["all", "char"]:
                    logging.info(f"Rendering character-level visualization for page {page_no}")
                    try:
                        img = page.render_as_image(
                            cell_unit=TextCellUnit.CHAR,
                            draw_cells_bbox=(not args.display_text),
                            draw_cells_text=args.display_text,
                        )
                        
                        # Save the image if an output directory was specified
                        if args.output_dir:
                            output_path = os.path.join(
                                args.output_dir, 
                                f"{os.path.basename(args.input_pdf)}.page_{page_no}.char.png"
                            )
                            img.save(output_path)
                            logging.info(f"Saved character-level visualization to {output_path}")
                        
                        # Show the image in interactive mode
                        if args.interactive:
                            img.show()
                    except Exception as e:
                        logging.error(f"Error rendering character-level visualization: {e}")
                    
                    # Log extracted text if requested
                    if args.log_text:
                        try:
                            # Check if textline_cells exist and have content
                            if hasattr(page, 'char_cells') and page.char_cells:
                                lines = []
                                for cell in page.char_cells:
                                    if hasattr(cell, 'text') and cell.text:
                                        lines.append(cell.text)
                                
                                logging.info(f"Character-level text (page {page_no}):")
                                print("\n".join(lines))
                            else:
                                logging.info(f"No character text found on page {page_no}")
                        except Exception as e:
                            logging.error(f"Error extracting character-level text: {e}")
                
                if args.category in ["all", "word"]:
                    logging.info(f"Rendering word-level visualization for page {page_no}")
                    try:
                        img = page.render_as_image(
                            cell_unit=TextCellUnit.WORD,
                            draw_cells_bbox=(not args.display_text),
                            draw_cells_text=args.display_text,
                        )
                        
                        # Save the image if an output directory was specified
                        if args.output_dir:
                            output_path = os.path.join(
                                args.output_dir, 
                                f"{os.path.basename(args.input_pdf)}.page_{page_no}.word.png"
                            )
                            img.save(output_path)
                            logging.info(f"Saved word-level visualization to {output_path}")
                        
                        # Show the image in interactive mode
                        if args.interactive:
                            img.show()
                    except Exception as e:
                        logging.error(f"Error rendering word-level visualization: {e}")
                    
                    # Log extracted text if requested
                    if args.log_text:
                        try:
                            # Check if word_cells exist and have content
                            if hasattr(page, 'word_cells') and page.word_cells:
                                lines = []
                                for cell in page.word_cells:
                                    if hasattr(cell, 'text') and cell.text:
                                        lines.append(cell.text)
                                
                                logging.info(f"Word-level text (page {page_no}):")
                                print("\n".join(lines))
                            else:
                                logging.info(f"No word text found on page {page_no}")
                        except Exception as e:
                            logging.error(f"Error extracting word-level text: {e}")
                
                if args.category in ["all", "line"]:
                    logging.info(f"Rendering line-level visualization for page {page_no}")
                    try:
                        img = page.render_as_image(
                            cell_unit=TextCellUnit.LINE,
                            draw_cells_bbox=(not args.display_text),
                            draw_cells_text=args.display_text,
                        )
                        
                        # Save the image if an output directory was specified
                        if args.output_dir:
                            output_path = os.path.join(
                                args.output_dir, 
                                f"{os.path.basename(args.input_pdf)}.page_{page_no}.line.png"
                            )
                            img.save(output_path)
                            logging.info(f"Saved line-level visualization to {output_path}")
                        
                        # Show the image in interactive mode
                        if args.interactive:
                            img.show()
                    except Exception as e:
                        logging.error(f"Error rendering line-level visualization: {e}")
                    
                    # Log extracted text if requested
                    if args.log_text:
                        try:
                            # Check if textline_cells exist and have content
                            if hasattr(page, 'textline_cells') and page.textline_cells:
                                lines = []
                                for cell in page.textline_cells:
                                    if hasattr(cell, 'text') and cell.text:
                                        lines.append(cell.text)
                                
                                logging.info(f"Line-level text (page {page_no}):")
                                print("\n".join(lines))
                            else:
                                logging.info(f"No line text found on page {page_no}")
                        except Exception as e:
                            logging.error(f"Error extracting line-level text: {e}")
            except Exception as e:
                logging.error(f"Error processing page {page_no}: {e}")
    
    except Exception as e:
        logging.error(f"Error processing PDF: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point for the script."""
    args = parse_args()
    visualize_pdf(args)


if __name__ == "__main__":
    main() 