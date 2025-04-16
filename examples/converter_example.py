#!/usr/bin/env python3
"""
Example script demonstrating the Docling converter usage.

This script shows how to use the convert_document function
to directly convert PDF documents to the Papermage format.
"""

import os
import sys
import json
from pprint import pprint

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the document converter
from papermage_docling import convert_document


def main():
    """Run the converter example."""
    print("Document Converter Example")
    print("======================")
    
    # Example: Convert a PDF file to Papermage format
    pdf_path = "examples/sample.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"\nExample PDF file not found: {pdf_path}")
        print("Please provide a sample PDF file to convert.")
        return
    
    print(f"\nConverting {pdf_path} to Papermage format using Docling...")
    try:
        # Convert directly using Docling
        result = convert_document(
            source=pdf_path,
            # Optional conversion parameters
            options={
                "enable_ocr": False,
                "detect_rtl": True,
                "detect_tables": True,
                "detect_figures": True
            }
        )
        
        print("\nConversion successful!")
        print(f"Document has {len(result.get('pages', []))} pages")
        
        # Save result to JSON file for inspection
        output_path = "examples/output_docling.json"
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"Conversion result saved to {output_path}")
    
    except Exception as e:
        print(f"Error during conversion: {str(e)}")


if __name__ == "__main__":
    main() 