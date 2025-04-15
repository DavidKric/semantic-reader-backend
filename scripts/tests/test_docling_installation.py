#!/usr/bin/env python3
"""
Test script to verify that Docling is correctly installed and working.
This script will attempt to use Docling's basic functionality to parse a sample PDF.
"""

import os
import sys
from pathlib import Path

try:
    from docling.documentconverter import DocumentConverter
    print("✅ Successfully imported Docling")
except ImportError as e:
    print(f"❌ Failed to import Docling: {e}")
    print("Please ensure Docling is installed with: pip install docling>=2.0.0")
    sys.exit(1)

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

def test_docling_basic_conversion(pdf_path=None):
    """Test basic PDF conversion with Docling."""
    if pdf_path is None:
        pdf_path = find_sample_pdf()
        if pdf_path is None:
            return False
    
    try:
        print(f"Testing Docling with file: {pdf_path}")
        converter = DocumentConverter(tables=True, figures=True)
        result = converter.convert(str(pdf_path))
        
        print("✅ Successfully converted PDF with Docling")
        
        # Check basic document structure
        doc = result.document
        print(f"Document has {len(doc.pages)} page(s)")
        
        # Check if tables were detected
        table_count = sum(1 for page in doc.pages for table in getattr(page, 'tables', []))
        print(f"Detected {table_count} table(s)")
        
        # Check if figures were detected
        figure_count = sum(1 for page in doc.pages for figure in getattr(page, 'figures', []))
        print(f"Detected {figure_count} figure(s)")
        
        return True
    except Exception as e:
        print(f"❌ Failed to convert PDF with Docling: {e}")
        return False

if __name__ == "__main__":
    # Allow passing a PDF path as argument
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    success = test_docling_basic_conversion(pdf_path)
    
    if success:
        print("\n✅ Docling is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Docling test failed.")
        sys.exit(1) 