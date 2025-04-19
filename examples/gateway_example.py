#!/usr/bin/env python3
"""
Example script demonstrating the DocumentGateway usage.

This script shows how to use the DocumentGateway interface to convert
PDF documents to the Papermage format used by the semantic reader.
"""

import json
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the document gateway
from papermage_docling.api.gateway import gateway


def main():
    """Run the gateway example."""
    print("Document Gateway Example")
    print("======================")
    
    # Print supported formats
    print("\nSupported format conversions:")
    formats = gateway.supported_formats()
    for source, targets in formats.items():
        print(f"  {source} -> {', '.join(targets)}")
    
    # Example: Convert a PDF file to Papermage format
    pdf_path = "examples/sample.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"\nExample PDF file not found: {pdf_path}")
        print("Please provide a sample PDF file to convert.")
        return
    
    print(f"\nConverting {pdf_path} to Papermage format...")
    try:
        # Convert using the gateway interface
        result = gateway.convert(
            document=pdf_path,
            source_format="pdf",
            target_format="papermage",
            # Optional conversion parameters
            enable_ocr=False,
            detect_rtl=True,
            detect_tables=True,
            detect_figures=True
        )
        
        print("\nConversion successful!")
        print(f"Document has {len(result.get('pages', []))} pages")
        
        # Save result to JSON file for inspection
        output_path = "examples/output.json"
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"Conversion result saved to {output_path}")
    
    except Exception as e:
        print(f"Error during conversion: {str(e)}")


if __name__ == "__main__":
    main() 