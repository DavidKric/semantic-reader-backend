#!/usr/bin/env python
"""
Docling PDF Visualizer

A simple wrapper for docling-parse's visualize.py that makes it easy to
visualize PDFs at char, word, and line levels without automatically opening images.

Usage:
    python docling_visualize.py --pdf <pdf_file> --output-dir <output_dir>

Options:
    --pdf <path>         Path to the PDF file to visualize
    --output-dir <path>  Directory to save visualization images (default: ./viz_output)
    --category <level>   Level of visualization [all, char, word, line] (default: all)
    --page <number>      Page number to visualize (-1 for all pages) (default: -1)
"""

import argparse
import logging
import os
import sys
import subprocess
from pathlib import Path


def check_and_install_dependencies():
    """Check if docling-parse is installed and install it if needed."""
    try:
        import docling_parse
        import docling_core
        logging.info("docling-parse and docling-core are installed.")
        return True
    except ImportError:
        logging.warning("docling-parse or docling-core not found. Attempting to install...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "docling-parse>=4.0.0"])
            logging.info("Successfully installed docling-parse.")
            return True
        except Exception as e:
            logging.error(f"Failed to install docling-parse: {e}")
            return False


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Visualize PDF files using docling-parse without auto-opening images"
    )
    parser.add_argument(
        "--pdf", "-p",
        required=True,
        help="Path to the PDF file to visualize"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="./viz_output",
        help="Directory to save visualization images"
    )
    parser.add_argument(
        "--category", "-c",
        choices=["all", "char", "word", "line"],
        default="all",
        help="Level of visualization"
    )
    parser.add_argument(
        "--page", "-n",
        type=int,
        default=-1,
        help="Page number to visualize (-1 for all pages)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def visualize_pdf_direct(pdf_path, output_dir, category="all", page_num=-1):
    """
    Visualize PDF directly using docling-parse, without importing the module.
    
    This is a direct approach that works even if docling-parse wasn't properly installed.
    """
    logging.info(f"Visualizing PDF using direct method: {pdf_path}")
    
    # Make sure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # First, try using the visualize_py function directly
    try:
        # Try explicit import
        from docling_parse.visualize import visualise_py
        
        # Call the function
        visualise_py(
            log_level="info",
            pdf_path=str(pdf_path),
            interactive=False,  # Don't show images
            output_dir=output_dir,
            display_text=False,
            log_text=False,
            category=category,
            page_num=page_num
        )
        
        generated_files = list(Path(output_dir).glob("*.png"))
        logging.info(f"Generated {len(generated_files)} visualization files")
        return True
    except Exception as e:
        logging.error(f"Failed to visualize using direct method: {e}")
        
        # Fallback: Use the command line approach
        try:
            logging.info("Trying fallback method using python -m docling_parse.visualize...")
            
            # Build the command
            cmd = [
                sys.executable,
                "-m", "docling_parse.visualize",
                "-i", str(pdf_path),
                "-c", category,
                "-o", str(output_dir)
            ]
            
            if page_num != -1:
                cmd.extend(["-p", str(page_num)])
                
            # Run the command
            subprocess.check_call(cmd)
            
            generated_files = list(Path(output_dir).glob("*.png"))
            logging.info(f"Generated {len(generated_files)} visualization files")
            return True
        except Exception as e2:
            logging.error(f"Failed to visualize using fallback method: {e2}")
            return False


def main():
    """Main entry point for the script."""
    args = parse_arguments()
    
    # Configure logging
    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    # Validate PDF path
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        logging.error(f"PDF file not found: {pdf_path}")
        return 1
    
    if not pdf_path.is_file() or pdf_path.suffix.lower() != '.pdf':
        logging.error(f"Not a valid PDF file: {pdf_path}")
        return 1
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        logging.info(f"Creating output directory: {output_dir}")
        os.makedirs(output_dir)
    
    # Check and install dependencies if needed
    check_and_install_dependencies()
    
    # Visualize the PDF
    success = visualize_pdf_direct(
        pdf_path=pdf_path,
        output_dir=output_dir,
        category=args.category,
        page_num=args.page
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 