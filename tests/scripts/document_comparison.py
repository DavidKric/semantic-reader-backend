#!/usr/bin/env python
"""
Document Comparison Script for PaperMage-Docling

This script processes sample PDF files and generates visualizations using
docling-parse's direct visualization capabilities. It creates visualizations
at char, word, and line levels without automatically opening them.

Features:
- Processes sample PDFs from different categories (simple, tables, multi-column, etc.)
- Generates char, word, and line level visualizations
- Produces HTML reports with all visualizations
- Supports batch processing with detailed logging

Usage:
    python document_comparison.py [options]

Options:
    --pdf PATH            Path to a specific PDF file to process
    --sample-type TYPE    Type of samples to process (simple, tables, multi_column, etc.)
    --output-dir DIR      Directory to save visualizations
    --enable-ocr          Enable OCR for scanned documents
    --no-tables           Disable table detection
    --no-figures          Disable figure detection
    --no-report           Disable HTML report generation
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Check for required libraries
try:
    # Import docling-parse for direct visualization
    from docling_core.types.doc.page import TextCellUnit
    from docling_parse.pdf_parser import DoclingPdfParser
    # Import report generation utilities
    from papermage_docling.visualizers.report_generator import generate_document_report
    DOCLING_AVAILABLE = True
except ImportError as e:
    logger.error(f"Required library not available: {e}")
    logger.error("Make sure docling-parse and papermage_docling are installed")
    DOCLING_AVAILABLE = False


def find_sample_files(sample_type: str) -> list[str]:
    """
    Find sample PDF files based on type.
    
    Args:
        sample_type: Type of samples to find ('simple', 'tables', 'multi_column', 'complex', 'corrupt', or 'all')
    
    Returns:
        List of file paths to sample PDFs
    
    Raises:
        FileNotFoundError: If no sample files are found
    """
    # Define the possible sample directories
    sample_dirs = []
    
    # Check tests/data/data directory (where most samples are located)
    data_dir = Path("tests/data/data")
    if data_dir.exists():
        sample_dirs.append(data_dir)
    
    # Also check tests/data/fixtures/samples if it exists
    fixtures_dir = Path("tests/data/fixtures/samples")
    if fixtures_dir.exists():
        sample_dirs.append(fixtures_dir)
    
    if not sample_dirs:
        raise FileNotFoundError(
            "Could not find sample directories. Make sure you're running from the project root "
            "and that either tests/data/data or tests/data/fixtures/samples exists."
        )
    
    # Define sample type patterns
    patterns = {
        "simple": ["sample1_simple.pdf"],
        "tables": ["sample*table*.pdf"],
        "multi_column": ["sample*column*.pdf", "*multicolumn*.pdf"],
        "complex": ["sample*complex*.pdf"],
        "corrupt": ["corrupt*.pdf", "broken*.pdf"],
        "all": ["*.pdf"]
    }
    
    if sample_type not in patterns:
        raise ValueError(f"Unknown sample type: {sample_type}. Valid types are: {', '.join(patterns.keys())}")
    
    # Find matching files
    sample_files = []
    pattern_list = patterns[sample_type]
    
    for directory in sample_dirs:
        for pattern in pattern_list:
            matched_files = list(directory.glob(pattern))
            sample_files.extend([str(f) for f in matched_files])
    
    # Log found files
    if sample_files:
        logging.info(f"Found {len(sample_files)} sample files of type '{sample_type}':")
        for f in sample_files:
            logging.info(f"  - {f}")
    else:
        raise FileNotFoundError(
            f"No sample files found for type '{sample_type}'. "
            f"Check that sample files exist in {', '.join(str(d) for d in sample_dirs)}"
        )
    
    return sample_files


def collect_document_stats(visualization_dir: str, pdf_file: str) -> Dict:
    """
    Collects statistics about the document processing results.
    
    Args:
        visualization_dir: Directory containing visualization outputs
        pdf_file: Path to the original PDF file
        
    Returns:
        Dictionary of document statistics
    """
    stats = {
        "processing_time": None,
        "page_count": 0,
        "entity_counts": {},
        "performance": {}
    }
    
    # Try to find stats file in the visualization directory
    stats_file = Path(visualization_dir) / "stats.json"
    if stats_file.exists():
        import json
        try:
            with open(stats_file, 'r') as f:
                stats.update(json.load(f))
        except Exception as e:
            logging.warning(f"Failed to load stats file: {e}")
    
    # If no stats file, try to infer some stats from the visualization outputs
    else:
        # Count the number of visualization pages
        viz_dir = Path(visualization_dir)
        char_viz_files = list(viz_dir.glob("*_char_*.png"))
        stats["page_count"] = len(char_viz_files)
        
        # Record file info
        file_size = Path(pdf_file).stat().st_size
        stats["file_info"] = {
            "size_bytes": file_size,
            "size_mb": round(file_size / (1024 * 1024), 2)
        }
    
    # Try to load raw data if available
    raw_data_file = Path(visualization_dir) / f"{Path(pdf_file).stem}_papermage.json"
    if raw_data_file.exists():
        import json
        try:
            with open(raw_data_file, 'r') as f:
                stats["raw_data"] = json.load(f)
                logging.info(f"Loaded raw data from {raw_data_file}")
        except Exception as e:
            logging.warning(f"Failed to load raw data file: {e}")
    
    return stats


def organize_visualizations(visualization_dir: str) -> Dict[str, Dict[int, str]]:
    """
    Organize visualization files by type and page number.
    
    Args:
        visualization_dir: Directory containing visualization outputs
        
    Returns:
        Dictionary mapping visualization types to page numbers and file paths
    """
    results = {
        "original": {},
        "char": {},
        "word": {},
        "line": {}
    }
    
    viz_dir = Path(visualization_dir)
    
    # Process visualization files for each level
    for img_file in viz_dir.glob("*.png"):
        filename = img_file.name
        
        # Parse the file to determine type and page number
        if "page_" in filename and ".pdf" in filename:
            parts = filename.split(".")
            for part in parts:
                if part.startswith("page_"):
                    try:
                        page_num = int(part.replace("page_", ""))
                        
                        if "char" in filename:
                            results["char"][page_num] = str(img_file)
                        elif "word" in filename:
                            results["word"][page_num] = str(img_file)
                        elif "line" in filename:
                            results["line"][page_num] = str(img_file)
                        elif "original" in filename or "orig" in filename:
                            results["original"][page_num] = str(img_file)
                            
                        break
                    except ValueError:
                        continue
    
    # Remove empty types
    return {k: v for k, v in results.items() if v}


def extract_metadata(pdf_file: str) -> Dict:
    """
    Extract metadata from the PDF file.
    
    Args:
        pdf_file: Path to the PDF file
        
    Returns:
        Dictionary of metadata
    """
    metadata = {
        "filename": os.path.basename(pdf_file),
        "file_size": os.path.getsize(pdf_file),
        "file_path": pdf_file
    }
    
    # Try to extract PDF metadata using PyPDF2
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_file)
        if reader.metadata:
            for key, value in reader.metadata.items():
                if key.startswith('/'):
                    key = key[1:]  # Remove leading slash from key
                metadata[key] = value
    except Exception as e:
        logging.warning(f"Failed to extract PDF metadata: {e}")
    
    return metadata


def parse_args():
    """
    Parse command-line arguments for the document comparison script.
    
    Returns:
        argparse.Namespace: The parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description="Generate document visualizations using docling-parse",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Input options - either a specific PDF or a sample type
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--pdf", "-p", 
        dest="pdf_path",
        help="Path to a specific PDF file to process"
    )
    input_group.add_argument(
        "--sample-type", "-s",
        choices=["simple", "tables", "multi_column", "complex", "corrupt", "all"],
        help="Type of sample files to process (if not specifying a PDF file)"
    )
    
    # Output configuration
    parser.add_argument(
        "--output-dir", "-o",
        default="./comparison_results",
        help="Directory to save visualizations"
    )
    
    # Feature toggles
    parser.add_argument(
        "--enable-ocr",
        action="store_true",
        help="Enable OCR during document processing"
    )
    parser.add_argument(
        "--no-tables",
        action="store_true",
        help="Disable table detection"
    )
    parser.add_argument(
        "--no-figures",
        action="store_true",
        help="Disable figure detection"
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Disable HTML report generation"
    )
    
    # Verbosity
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging based on verbosity
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    
    return args


def generate_visualizations(
    pdf_file: str, 
    output_dir: Path,
) -> Dict[str, Dict[int, str]]:
    """
    Generate visualizations for a PDF document using docling-parse directly.
    
    Args:
        pdf_file: Path to the PDF file
        output_dir: Directory to save visualizations
        
    Returns:
        Dictionary mapping visualization types to page numbers and file paths
    """
    try:
        if not DOCLING_AVAILABLE:
            raise ImportError("docling-parse is not available")
        
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Use docling-parse directly
        parser = DoclingPdfParser(loglevel="error")
        pdf_doc = parser.load(path_or_stream=pdf_file, lazy=True)
        
        visualizations = {
            "char": {},
            "word": {},
            "line": {}
        }
        
        # Process each page
        for page_no in range(1, pdf_doc.number_of_pages() + 1):
            logging.info(f"Processing page {page_no} of {pdf_file}")
            
            pdf_page = pdf_doc.get_page(page_no=page_no)
            base_filename = os.path.basename(pdf_file)
            
            # Generate character-level visualization
            img = pdf_page.render_as_image(
                cell_unit=TextCellUnit.CHAR,
                draw_cells_bbox=True,
                draw_cells_text=False
            )
            char_path = f"{output_dir}/{base_filename}.page_{page_no}.char.png"
            img.save(char_path)
            visualizations["char"][page_no] = char_path
            
            # Generate word-level visualization
            img = pdf_page.render_as_image(
                cell_unit=TextCellUnit.WORD,
                draw_cells_bbox=True,
                draw_cells_text=False
            )
            word_path = f"{output_dir}/{base_filename}.page_{page_no}.word.png"
            img.save(word_path)
            visualizations["word"][page_no] = word_path
            
            # Generate line-level visualization
            img = pdf_page.render_as_image(
                cell_unit=TextCellUnit.LINE,
                draw_cells_bbox=True,
                draw_cells_text=False
            )
            line_path = f"{output_dir}/{base_filename}.page_{page_no}.line.png"
            img.save(line_path)
            visualizations["line"][page_no] = line_path
            
            # Generate original page visualization if possible
            try:
                # Create original page image without cell_unit parameter
                # This is a direct PDF page rendering
                from PIL import Image
                import fitz  # PyMuPDF
                
                # Open the PDF and render the page as an image
                pdf = fitz.open(pdf_file)
                pix = pdf[page_no-1].get_pixmap(matrix=fitz.Matrix(2, 2))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                orig_path = f"{output_dir}/{base_filename}.page_{page_no}.original.png"
                img.save(orig_path)
                if "original" not in visualizations:
                    visualizations["original"] = {}
                visualizations["original"][page_no] = orig_path
            except Exception as e:
                logging.warning(f"Failed to render original page {page_no}: {e}")
        
        # Save raw JSON data for the document if possible
        try:
            import json
            raw_data = pdf_doc.to_dict() if hasattr(pdf_doc, 'to_dict') else {}
            
            # Add additional raw data from the PDF document
            if not raw_data:
                # Create a basic structure if to_dict() is not available
                raw_data = {
                    "number_of_pages": pdf_doc.number_of_pages(),
                    "metadata": pdf_doc.document_info if hasattr(pdf_doc, 'document_info') else {},
                }
            
            # Save raw data to a JSON file
            raw_data_path = f"{output_dir}/{Path(pdf_file).stem}_papermage.json"
            with open(raw_data_path, 'w') as f:
                json.dump(raw_data, f, indent=2)
            logging.info(f"Saved raw JSON data to {raw_data_path}")
            
        except Exception as e:
            logging.warning(f"Failed to save raw JSON data: {e}")
        
        logging.info(f"Generated visualizations for {pdf_file}")
        return visualizations
        
    except Exception as e:
        logging.error(f"Failed to generate visualizations for {pdf_file}: {e}")
        if "corrupt" in pdf_file:
            logging.info("This error may be expected for corrupt sample files")
        else:
            logging.exception("Details:")
        return {}


def main():
    """
    Main entry point for the document comparison script.
    """
    start_time = time.time()
    args = parse_args()
    
    # Check if docling-parse is available
    if not DOCLING_AVAILABLE:
        logging.error("docling-parse is not available. Please install it first.")
        return 1
    
    # Find input files
    input_files = []
    try:
        if args.pdf_path:
            # Use specific PDF file
            pdf_path = Path(args.pdf_path)
            if not pdf_path.exists():
                logging.error(f"PDF file not found: {pdf_path}")
                return 1
            if not pdf_path.is_file() or pdf_path.suffix.lower() != '.pdf':
                logging.error(f"Not a valid PDF file: {pdf_path}")
                return 1
            input_files = [str(pdf_path)]
        else:
            # Use sample files
            input_files = find_sample_files(args.sample_type)
    except (FileNotFoundError, ValueError) as e:
        logging.error(str(e))
        return 1
    
    if not input_files:
        logging.error("No input files to process")
        return 1
    
    # Create output directory
    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        logging.info(f"Creating output directory: {output_dir}")
        os.makedirs(output_dir)
    
    # Process each sample file
    success_count = 0
    failure_count = 0
    report_paths = []
    
    for pdf_file in input_files:
        logging.info(f"Processing: {pdf_file}")
        
        # Create a subdirectory for each sample if processing multiple files
        if len(input_files) > 1:
            sample_output_dir = output_dir / Path(pdf_file).stem
            if not sample_output_dir.exists():
                os.makedirs(sample_output_dir)
        else:
            sample_output_dir = output_dir
        
        # Generate visualizations directly using docling-parse
        visualizations = generate_visualizations(pdf_file, sample_output_dir)
        
        if visualizations:
            success_count += 1
            
            # Generate report if enabled
            if not args.no_report:
                try:
                    # Extract metadata and stats
                    metadata = extract_metadata(pdf_file)
                    document_stats = collect_document_stats(str(sample_output_dir), pdf_file)
                    
                    # Generate HTML report
                    report_path = str(sample_output_dir / f"{Path(pdf_file).stem}_report.html")
                    
                    report_path = generate_document_report(
                        output_path=report_path,
                        title=f"Document Analysis: {Path(pdf_file).stem}",
                        filename=Path(pdf_file).name,
                        visualizations=visualizations,
                        metadata=metadata,
                        document_stats=document_stats
                    )
                    
                    logging.info(f"Generated report: {report_path}")
                    report_paths.append(report_path)
                    
                except Exception as e:
                    logging.error(f"Failed to generate report for {pdf_file}: {e}")
                    logging.exception("Details:")
        else:
            failure_count += 1
    
    # Report results
    total = len(input_files)
    elapsed_time = time.time() - start_time
    logging.info(f"Processed {total} documents in {elapsed_time:.2f} seconds: {success_count} successful, {failure_count} failed")
    
    if report_paths:
        logging.info(f"Generated {len(report_paths)} HTML reports:")
        for path in report_paths:
            logging.info(f"  - {path}")
    
    return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main()) 