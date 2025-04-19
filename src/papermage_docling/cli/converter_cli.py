#!/usr/bin/env python3
"""
Command-line interface for converting between Docling document formats and PaperMage.

This module provides a command-line tool for converting DoclingDocument and PdfDocument 
instances to PaperMage-compatible Document formats, and saving the results to JSON.
"""

import argparse
import json
import logging
import sys
from typing import Any, Dict

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("docling-converter")

# Try to import Docling dependencies
try:
    from docling_core.types import DoclingDocument
    from docling_parse.pdf_parser import DoclingPdfParser as DoclingPdfParserBase
    from docling_parse.pdf_parser import PdfDocument
    HAS_DOCLING = True
except ImportError:
    logger.warning("Docling dependencies not found. Limited functionality available.")
    HAS_DOCLING = False

# Import our converter
from papermage_docling.converters.docling_to_papermage_converter import (
    DoclingToPaperMageConverter,
)


def save_json(data: Dict[str, Any], output_path: str) -> None:
    """
    Save data as JSON to the specified path.
    
    Args:
        data: Dictionary to save as JSON
        output_path: Output file path
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved JSON to {output_path}")


def convert_pdf(input_path: str, output_path: str, enable_ocr: bool = False, 
                language: str = None, detect_rtl: bool = False) -> None:
    """
    Convert a PDF file to PaperMage JSON format.
    
    Args:
        input_path: Path to input PDF file
        output_path: Path to output JSON file
        enable_ocr: Whether to enable OCR during parsing
        language: OCR language code
        detect_rtl: Whether to detect and process RTL text
    """
    if not HAS_DOCLING:
        logger.error("Cannot convert PDF without Docling dependencies")
        sys.exit(1)
    
    logger.info(f"Converting PDF at {input_path} to PaperMage JSON format")
    
    # Parse PDF using Docling parser
    try:
        parser = DoclingPdfParserBase(enable_ocr=enable_ocr, ocr_language=language)
        pdf_doc = parser.load(input_path)
        logger.info(f"Successfully parsed PDF with {len(pdf_doc.pages)} pages")
    except Exception as e:
        logger.error(f"Failed to parse PDF: {e}")
        sys.exit(1)
    
    # Convert to PaperMage format
    try:
        converter = DoclingToPaperMageConverter()
        papermage_doc = converter.convert_pdf_document(pdf_doc)
        logger.info("Successfully converted PDF document to PaperMage format")
    except Exception as e:
        logger.error(f"Failed to convert document: {e}")
        sys.exit(1)
    
    # Save as JSON
    try:
        json_data = papermage_doc.to_json()
        save_json(json_data, output_path)
    except Exception as e:
        logger.error(f"Failed to save JSON: {e}")
        sys.exit(1)


def convert_docling_json(input_path: str, output_path: str) -> None:
    """
    Convert a Docling JSON file to PaperMage JSON format.
    
    Args:
        input_path: Path to input Docling JSON file
        output_path: Path to output PaperMage JSON file
    """
    if not HAS_DOCLING:
        logger.error("Cannot convert Docling JSON without Docling dependencies")
        sys.exit(1)
    
    logger.info(f"Converting Docling JSON at {input_path} to PaperMage JSON format")
    
    # Load Docling JSON
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            docling_data = json.load(f)
        
        # Convert to DoclingDocument
        docling_doc = DoclingDocument.model_validate(docling_data)
        logger.info("Successfully loaded Docling document from JSON")
    except Exception as e:
        logger.error(f"Failed to load Docling JSON: {e}")
        sys.exit(1)
    
    # Convert to PaperMage format
    try:
        converter = DoclingToPaperMageConverter()
        papermage_doc = converter.convert_docling_document(docling_doc)
        logger.info("Successfully converted Docling document to PaperMage format")
    except Exception as e:
        logger.error(f"Failed to convert document: {e}")
        sys.exit(1)
    
    # Save as JSON
    try:
        json_data = papermage_doc.to_json()
        save_json(json_data, output_path)
    except Exception as e:
        logger.error(f"Failed to save JSON: {e}")
        sys.exit(1)


def validate_papermage_json(input_path: str) -> None:
    """
    Validate that a JSON file conforms to PaperMage format.
    
    Args:
        input_path: Path to PaperMage JSON file to validate
    """
    logger.info(f"Validating PaperMage JSON at {input_path}")
    
    # Load JSON
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON: {e}")
        sys.exit(1)
    
    # Validate format
    try:
        from papermage_docling.converters.document import Document
        doc = Document.from_json(data)
        DoclingToPaperMageConverter.validate_papermage_format(doc)
        logger.info("✅ JSON is valid PaperMage format")
    except Exception as e:
        logger.error(f"❌ JSON is not valid PaperMage format: {e}")
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Convert between Docling document formats and PaperMage JSON."
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # PDF conversion command
    pdf_parser = subparsers.add_parser(
        "pdf", help="Convert a PDF file to PaperMage JSON format using Docling"
    )
    pdf_parser.add_argument("input", help="Path to input PDF file")
    pdf_parser.add_argument("output", help="Path to output JSON file")
    pdf_parser.add_argument(
        "--ocr", action="store_true", help="Enable OCR for text extraction"
    )
    pdf_parser.add_argument(
        "--language", help="OCR language code (e.g., 'eng', 'ara')"
    )
    pdf_parser.add_argument(
        "--rtl", action="store_true", help="Detect and process RTL text"
    )
    
    # Docling JSON conversion command
    docling_parser = subparsers.add_parser(
        "docling", help="Convert a Docling JSON file to PaperMage JSON format"
    )
    docling_parser.add_argument("input", help="Path to input Docling JSON file")
    docling_parser.add_argument("output", help="Path to output PaperMage JSON file")
    
    # Validation command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate that a JSON file conforms to PaperMage format"
    )
    validate_parser.add_argument("input", help="Path to PaperMage JSON file to validate")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == "pdf":
        convert_pdf(
            args.input, args.output, 
            enable_ocr=args.ocr, 
            language=args.language, 
            detect_rtl=args.rtl
        )
    elif args.command == "docling":
        convert_docling_json(args.input, args.output)
    elif args.command == "validate":
        validate_papermage_json(args.input)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main() 