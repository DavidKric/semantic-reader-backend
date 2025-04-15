#!/usr/bin/env python3
"""
Demo script for the refactored Docling-native implementation.
This script demonstrates the use of the new converter to process a document.
"""

import os
import sys
import json
from pathlib import Path
from pprint import pprint

# Add the src directory to Python path
src_path = Path(__file__).resolve().parents[1] / "src"
sys.path.append(str(src_path))

def find_sample_pdf():
    """Find a sample PDF file to test with."""
    # Look in common directories for a PDF file
    search_dirs = [
        Path("examples"),
        Path("tests/fixtures"),
        Path("tests/data"),
        Path("tests"),
        Path("docs"),
        Path("."),
    ]
    
    for directory in search_dirs:
        if not directory.exists():
            continue
        
        for file in directory.glob("**/*.pdf"):
            print(f"Found sample PDF: {file}")
            return file
    
    print("No sample PDF found. Please provide a PDF file path to test with.")
    return None

def demo_converter(pdf_path=None):
    """Demonstrate the new converter."""
    # Import the new converter
    try:
        from papermage_docling.converter import convert_document
        print("✅ Successfully imported the new converter")
    except ImportError as e:
        print(f"❌ Failed to import converter: {e}")
        sys.exit(1)
    
    # Find a PDF file if one wasn't provided
    if pdf_path is None:
        pdf_path = find_sample_pdf()
        if pdf_path is None:
            print("❌ No PDF file found to test with")
            sys.exit(1)
    
    print(f"\nProcessing document: {pdf_path}\n")
    
    # Set conversion options
    options = {
        "detect_tables": True,
        "detect_figures": True,
        "enable_ocr": False
    }
    
    # Process the document
    try:
        result = convert_document(str(pdf_path), options=options)
        print("✅ Successfully converted document with Docling")
        
        # Print basic information about the document
        print(f"\nDocument Information:")
        print(f"- Number of pages: {len(result.get('pages', []))}")
        
        # Check if tables and figures were detected
        if 'entities' in result:
            tables = result['entities'].get('tables', [])
            figures = result['entities'].get('figures', [])
            print(f"- Number of tables: {len(tables)}")
            print(f"- Number of figures: {len(figures)}")
        
        # Print metadata if available
        if 'metadata' in result:
            print(f"\nMetadata:")
            for key, value in result['metadata'].items():
                print(f"- {key}: {value}")
        
        # Save the result to a JSON file for inspection
        output_dir = Path("scripts/output")
        output_dir.mkdir(exist_ok=True, parents=True)
        output_file = output_dir / "refactored_output.json"
        
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"\nOutput saved to {output_file}")
        print("\n✅ Demo completed successfully!")
        return True
    
    except Exception as e:
        print(f"❌ Failed to convert document: {e}")
        return False

if __name__ == "__main__":
    # Allow passing a PDF path as argument
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    success = demo_converter(pdf_path)
    sys.exit(0 if success else 1) 