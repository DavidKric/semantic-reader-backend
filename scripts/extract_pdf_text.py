#!/usr/bin/env python3
"""
PDF Text Extraction Script using DoclingPdfParser

This script extracts text from PDF files using DoclingPdfParser,
with support for RTL text and language detection.
"""

import argparse
import logging
import os
import json
from pathlib import Path
import sys

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import our DoclingPdfParser
from src.papermage_docling.parsers import DoclingPdfParser

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Extract text from PDF files.")

    # Add an argument for the path to the PDF file
    parser.add_argument(
        "-i", "--input-pdf", type=str, help="Path to the PDF file", required=True
    )
    
    # Add an argument for the output directory
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=False,
        default=None,
        help="Output file path (default: input filename + .txt)",
    )
    
    # Add an argument for the output format
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format: 'text' or 'json' (default: text)",
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
    
    # Add an argument for specifying a page number
    parser.add_argument(
        "-p",
        "--page",
        type=int,
        required=False,
        default=-1,
        help="Page to process (default: -1 -> all pages)",
    )

    # Parse the command-line arguments
    args = parser.parse_args()

    # Check if the PDF file exists
    if not os.path.exists(args.input_pdf):
        parser.error(f"PDF file does not exist: {args.input_pdf}")

    # Set default output path if not specified
    if args.output is None:
        if args.format == "text":
            args.output = f"{os.path.splitext(args.input_pdf)[0]}.txt"
        else:
            args.output = f"{os.path.splitext(args.input_pdf)[0]}.json"

    return args


def extract_pdf_text(args):
    """
    Extract text from a PDF using DoclingPdfParser.
    
    Args:
        args: Command-line arguments
    """
    # Initialize the parser with the specified options
    parser = DoclingPdfParser(
        detect_rtl=args.rtl,
        enable_language_detection=args.language_detection
    )
    
    try:
        # Parse in desired format
        if args.format == "json":
            # Parse to PaperMage format for structured JSON output
            doc = parser.parse(
                args.input_pdf, 
                output_format='papermage'
            )
            
            # Get structured data
            result = {
                "text": doc.symbols,
                "metadata": doc.metadata,
                "pages": []
            }
            
            # Add page data
            pages = doc.get_entity_layer('pages')
            for i, page in enumerate(pages):
                page_data = {
                    "page_number": i + 1,
                    "text": page.text if hasattr(page, 'text') else "",
                    "metadata": page.metadata if hasattr(page, 'metadata') else {}
                }
                
                # Add text lines if available
                lines = []
                rows = doc.get_entity_layer('rows')
                for row in rows:
                    if hasattr(row, 'boxes') and row.boxes and row.boxes[0].page == i:
                        lines.append({
                            "text": row.text,
                            "is_rtl": row.metadata.get("is_rtl", False) if hasattr(row, 'metadata') else False
                        })
                
                page_data["lines"] = lines
                result["pages"].append(page_data)
            
            # Write JSON output
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logging.info(f"Extracted text data saved to {args.output}")
            
            # Print summary
            logging.info(f"Document summary:")
            logging.info(f"- Pages: {len(result['pages'])}")
            logging.info(f"- Text length: {len(result['text'])} characters")
            if "language_name" in result["metadata"]:
                logging.info(f"- Language: {result['metadata']['language_name']} (confidence: {result['metadata'].get('language_confidence', 0):.2f})")
            if "has_rtl" in result["metadata"] and result["metadata"]["has_rtl"]:
                logging.info(f"- RTL content detected: {result['metadata'].get('rtl_lines_count', 0)} lines")
        
        else:
            # Parse to native format for simple text extraction
            doc = parser.parse(
                args.input_pdf, 
                output_format='docling'
            )
            
            # Extract text from all pages or a specific page
            page_nos = [args.page]
            if args.page == -1:
                page_nos = list(range(doc.number_of_pages()))
            
            # Open the output file
            with open(args.output, 'w', encoding='utf-8') as f:
                # Add document metadata
                if hasattr(doc, 'metadata'):
                    f.write("=== DOCUMENT METADATA ===\n")
                    for key, value in doc.metadata.items():
                        f.write(f"{key}: {value}\n")
                    f.write("\n=== DOCUMENT TEXT ===\n\n")
                
                # Process each page
                for page_idx, page in doc.iterate_pages():
                    if page_idx not in page_nos and args.page != -1:
                        continue
                    
                    # Write page separator
                    f.write(f"--- Page {page_idx + 1} ---\n")
                    
                    # Extract and write text from textline cells
                    if hasattr(page, 'textline_cells') and page.textline_cells:
                        for cell in page.textline_cells:
                            if hasattr(cell, 'text') and cell.text:
                                f.write(cell.text + "\n")
                    
                    f.write("\n")
            
            logging.info(f"Extracted text saved to {args.output}")
    
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point for the script."""
    args = parse_args()
    extract_pdf_text(args)


if __name__ == "__main__":
    main()