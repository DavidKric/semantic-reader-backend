#!/usr/bin/env python3
"""
PDF Comparison Script for DoclingPdfParser

This script compares the parsing results between different PDF files,
useful for evaluating RTL detection and language detection capabilities.
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

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
    parser = argparse.ArgumentParser(description="Compare PDF parsing results.")

    # Add arguments for input PDF files (2 or more)
    parser.add_argument(
        "-i", "--input-pdfs", nargs="+", help="Paths to PDF files to compare", required=True
    )
    
    # Add an argument for the output directory
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=False,
        default=None,
        help="Output JSON file path (default: comparison_results.json)",
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
    
    # Add option to limit pages
    parser.add_argument(
        "--max-pages",
        type=int,
        required=False,
        default=-1,
        help="Maximum number of pages to process per document (default: -1 -> all pages)",
    )

    # Parse the command-line arguments
    args = parser.parse_args()

    # Check if the PDF files exist
    for pdf_path in args.input_pdfs:
        if not os.path.exists(pdf_path):
            parser.error(f"PDF file does not exist: {pdf_path}")
    
    # Set default output path if not specified
    if args.output is None:
        args.output = "comparison_results.json"

    return args


def parse_pdf(pdf_path: str, enable_rtl: bool, enable_language_detection: bool, max_pages: int = -1) -> Dict[str, Any]:
    """
    Parse a PDF and extract key information for comparison.
    
    Args:
        pdf_path: Path to the PDF file
        enable_rtl: Whether to enable RTL detection
        enable_language_detection: Whether to enable language detection
        max_pages: Maximum number of pages to process
        
    Returns:
        A dictionary containing parsed information
    """
    # Initialize the parser
    parser = DoclingPdfParser(
        detect_rtl=enable_rtl,
        enable_language_detection=enable_language_detection
    )
    
    # Start timing
    start_time = time.time()
    
    # Parse document in papermage format for structured data
    papermage_doc = parser.parse(
        pdf_path, 
        output_format='papermage',
        lazy=False
    )
    
    # Calculate processing time
    processing_time = time.time() - start_time
    
    # Gather metadata from parsed document
    result = {
        "filename": os.path.basename(pdf_path),
        "path": pdf_path,
        "processing_time_seconds": processing_time,
        "total_pages": len(papermage_doc.get_entity_layer('pages')),
        "total_text_length": len(papermage_doc.symbols),
        "metadata": papermage_doc.metadata,
        "language_info": {},
        "rtl_info": {},
        "page_summary": []
    }
    
    # Extract language information if detected
    if "language" in papermage_doc.metadata:
        result["language_info"] = {
            "language": papermage_doc.metadata.get("language", "unknown"),
            "language_name": papermage_doc.metadata.get("language_name", "Unknown"),
            "confidence": papermage_doc.metadata.get("language_confidence", 0.0),
            "is_rtl_language": papermage_doc.metadata.get("is_rtl_language", False)
        }
    
    # Extract RTL information if detected
    if "has_rtl" in papermage_doc.metadata and papermage_doc.metadata["has_rtl"]:
        result["rtl_info"] = {
            "has_rtl": True,
            "rtl_lines_count": papermage_doc.metadata.get("rtl_lines_count", 0),
            "rtl_pages": papermage_doc.metadata.get("rtl_pages", [])
        }
    else:
        result["rtl_info"] = {
            "has_rtl": False,
            "rtl_lines_count": 0,
            "rtl_pages": []
        }
    
    # Limit pages if specified
    pages = papermage_doc.get_entity_layer('pages')
    rows = papermage_doc.get_entity_layer('rows')
    
    page_count = len(pages)
    pages_to_process = page_count if max_pages <= 0 else min(max_pages, page_count)
    
    # Get page summaries
    for page_idx in range(pages_to_process):
        page_info = {
            "page_number": page_idx + 1,
            "total_rows": 0,
            "rtl_rows": 0,
            "sample_text": ""
        }
        
        # Count rows in this page
        page_rows = [row for row in rows if hasattr(row, 'boxes') and row.boxes and row.boxes[0].page == page_idx]
        page_info["total_rows"] = len(page_rows)
        
        # Count RTL rows
        rtl_rows = [row for row in page_rows if hasattr(row, 'metadata') and row.metadata.get("is_rtl", False)]
        page_info["rtl_rows"] = len(rtl_rows)
        
        # Get a sample text from the page
        if page_rows:
            page_info["sample_text"] = page_rows[0].text if hasattr(page_rows[0], 'text') else ""
        
        result["page_summary"].append(page_info)
    
    return result


def compare_pdfs(args):
    """
    Compare multiple PDF files and generate a comparison report.
    
    Args:
        args: Command-line arguments
    """
    comparison_results = {
        "comparison_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "rtl_detection_enabled": args.rtl,
        "language_detection_enabled": args.language_detection,
        "pdf_count": len(args.input_pdfs),
        "max_pages_processed": args.max_pages,
        "results": []
    }
    
    # Process each PDF
    for pdf_path in args.input_pdfs:
        logging.info(f"Processing {pdf_path}...")
        
        try:
            result = parse_pdf(
                pdf_path, 
                args.rtl, 
                args.language_detection, 
                args.max_pages
            )
            comparison_results["results"].append(result)
            
            # Log some basic information
            logging.info(f"Completed parsing {os.path.basename(pdf_path)}:")
            logging.info(f"- Pages: {result['total_pages']}")
            logging.info(f"- Text length: {result['total_text_length']} characters")
            if result["language_info"]:
                lang_name = result["language_info"].get("language_name", "Unknown")
                confidence = result["language_info"].get("confidence", 0.0)
                logging.info(f"- Language: {lang_name} (confidence: {confidence:.2f})")
            if result["rtl_info"]["has_rtl"]:
                logging.info(f"- RTL content detected: {result['rtl_info']['rtl_lines_count']} lines")
            else:
                logging.info("- No RTL content detected")
        
        except Exception as e:
            logging.error(f"Error processing {pdf_path}: {e}")
            import traceback
            traceback.print_exc()
    
    # Compute comparison metrics
    if len(comparison_results["results"]) > 1:
        comparison_results["comparisons"] = []
        
        for i, result1 in enumerate(comparison_results["results"]):
            for j, result2 in enumerate(comparison_results["results"][i+1:], i+1):
                comparison = {
                    "file1": result1["filename"],
                    "file2": result2["filename"],
                    "differences": {}
                }
                
                # Compare language detection
                if result1["language_info"] and result2["language_info"]:
                    same_language = result1["language_info"].get("language") == result2["language_info"].get("language")
                    comparison["differences"]["same_language"] = same_language
                    
                    if not same_language:
                        comparison["differences"]["language_info"] = {
                            "file1": result1["language_info"],
                            "file2": result2["language_info"]
                        }
                
                # Compare RTL detection
                if result1["rtl_info"] and result2["rtl_info"]:
                    same_rtl_status = result1["rtl_info"]["has_rtl"] == result2["rtl_info"]["has_rtl"]
                    comparison["differences"]["same_rtl_status"] = same_rtl_status
                    
                    if not same_rtl_status:
                        comparison["differences"]["rtl_info"] = {
                            "file1": result1["rtl_info"],
                            "file2": result2["rtl_info"]
                        }
                
                # Compare page counts
                comparison["differences"]["page_count_difference"] = result1["total_pages"] - result2["total_pages"]
                
                # Compare processing times
                comparison["differences"]["processing_time_ratio"] = (
                    result1["processing_time_seconds"] / max(0.001, result2["processing_time_seconds"])
                )
                
                comparison_results["comparisons"].append(comparison)
    
    # Save results to JSON
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(comparison_results, f, indent=2, ensure_ascii=False)
    
    logging.info(f"Comparison results saved to {args.output}")
    
    # Print overall summary
    logging.info("\nComparison Summary:")
    logging.info(f"- PDFs compared: {len(comparison_results['results'])}")
    
    if "comparisons" in comparison_results:
        same_language_count = sum(1 for comp in comparison_results["comparisons"] 
                                 if comp["differences"].get("same_language", True))
        same_rtl_count = sum(1 for comp in comparison_results["comparisons"] 
                            if comp["differences"].get("same_rtl_status", True))
        
        total_comparisons = len(comparison_results["comparisons"])
        if total_comparisons > 0:
            logging.info(f"- Language detection consistency: {same_language_count}/{total_comparisons} ({same_language_count/total_comparisons:.1%})")
            logging.info(f"- RTL detection consistency: {same_rtl_count}/{total_comparisons} ({same_rtl_count/total_comparisons:.1%})")


def main():
    """Main entry point for the script."""
    args = parse_args()
    compare_pdfs(args)


if __name__ == "__main__":
    main() 