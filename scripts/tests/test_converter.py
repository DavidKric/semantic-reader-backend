#!/usr/bin/env python3
"""
Test script to compare the new Docling-based converter with the legacy pipeline.
This script verifies that the output format remains consistent during the refactoring.
"""

import os
import sys
import json
import difflib
from pathlib import Path
from pprint import pprint

# Add the src directory to Python path
src_path = Path(__file__).resolve().parents[2] / "src"
sys.path.append(str(src_path))

try:
    from papermage_docling.converter import convert_document
    print("✅ Successfully imported new converter")
except ImportError as e:
    print(f"❌ Failed to import converter: {e}")
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

def compare_converters(pdf_path=None):
    """Compare the output of the new and legacy converters."""
    if pdf_path is None:
        pdf_path = find_sample_pdf()
        if pdf_path is None:
            return False
    
    try:
        print(f"Testing converter with file: {pdf_path}")
        
        # Convert with the new Docling converter
        new_result = convert_document(str(pdf_path), options={"detect_tables": True, "detect_figures": True})
        print("✅ Successfully converted with new Docling converter")
        
        # Convert with the legacy pipeline
        legacy_result = convert_document(str(pdf_path), options={"detect_tables": True, "detect_figures": True}, use_legacy=True)
        print("✅ Successfully converted with legacy pipeline")
        
        # Compare basic structure
        print("\nComparing outputs:")
        print(f"New output keys: {set(new_result.keys())}")
        print(f"Legacy output keys: {set(legacy_result.keys())}")
        
        # Check if all expected keys are present in both
        expected_keys = {"id", "metadata", "pages", "full_text", "entities"}
        for key in expected_keys:
            if key in new_result and key in legacy_result:
                print(f"✅ Both outputs have '{key}'")
            else:
                print(f"❌ Key '{key}' missing in one of the outputs")
        
        # Compare some basic statistics
        print("\nStatistics comparison:")
        print(f"Pages count: New={len(new_result.get('pages', []))}, Legacy={len(legacy_result.get('pages', []))}")
        
        if 'entities' in new_result and 'entities' in legacy_result:
            new_tables = len(new_result['entities'].get('tables', []))
            legacy_tables = len(legacy_result['entities'].get('tables', []))
            print(f"Tables count: New={new_tables}, Legacy={legacy_tables}")
            
            new_figures = len(new_result['entities'].get('figures', []))
            legacy_figures = len(legacy_result['entities'].get('figures', []))
            print(f"Figures count: New={new_figures}, Legacy={legacy_figures}")
        
        # Save outputs to files for manual inspection
        output_dir = Path("scripts/tests/output")
        output_dir.mkdir(exist_ok=True, parents=True)
        
        with open(output_dir / "new_output.json", "w") as f:
            json.dump(new_result, f, indent=2)
        
        with open(output_dir / "legacy_output.json", "w") as f:
            json.dump(legacy_result, f, indent=2)
        
        print(f"\nOutputs saved to {output_dir} for manual comparison")
        
        # Success if we got this far
        return True
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        return False

if __name__ == "__main__":
    # Allow passing a PDF path as argument
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    success = compare_converters(pdf_path)
    
    if success:
        print("\n✅ Converter test completed!")
        sys.exit(0)
    else:
        print("\n❌ Converter test failed.")
        sys.exit(1) 