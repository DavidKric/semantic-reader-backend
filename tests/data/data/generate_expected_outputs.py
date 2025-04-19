#!/usr/bin/env python
"""
Script to generate expected JSON outputs for sample PDFs.

This script processes each sample PDF through the document processing pipeline
and saves the output as JSON files in the expected/ directory.
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to Python path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the necessary modules
try:
    from app.services.pipeline_service import PipelineService
except ImportError:
    print("Error: Could not import PipelineService. Make sure the application is properly installed.")
    sys.exit(1)

# Define paths
DATA_DIR = Path(__file__).parent
EXPECTED_DIR = DATA_DIR / "expected"

# Ensure expected directory exists
EXPECTED_DIR.mkdir(exist_ok=True, parents=True)


def process_pdf(pdf_path):
    """
    Process a PDF file and return the JSON output.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        dict: The JSON output from processing the PDF
    """
    # Create a pipeline service instance
    pipeline_service = PipelineService()
    
    try:
        # Process the document
        print(f"Processing {pdf_path.name}...")
        result = pipeline_service.process_document(str(pdf_path))
        return result
    except Exception as e:
        print(f"Error processing {pdf_path.name}: {e}")
        return None


def generate_expected_outputs(force=False):
    """
    Generate expected JSON outputs for all sample PDFs.
    
    Args:
        force: If True, overwrite existing expected outputs
    """
    # Find all PDF files in the data directory
    pdf_files = list(DATA_DIR.glob("*.pdf"))
    
    # Skip the corrupted PDF - it's not meant to be processed successfully
    pdf_files = [pdf for pdf in pdf_files if pdf.name != "corrupt.pdf"]
    
    if not pdf_files:
        print("No PDF files found. Run download_samples.py first.")
        return
    
    print(f"Found {len(pdf_files)} PDF files.")
    
    for pdf_path in pdf_files:
        expected_json_path = EXPECTED_DIR / f"{pdf_path.stem}.json"
        
        # Skip if the expected output already exists and force is False
        if expected_json_path.exists() and not force:
            print(f"Skipping {pdf_path.name} - expected output already exists. Use --force to overwrite.")
            continue
        
        # Process the PDF
        result = process_pdf(pdf_path)
        
        if result:
            # Save the result as the expected output
            with open(expected_json_path, "w") as f:
                json.dump(result, f, indent=2)
            print(f"✓ Created expected output: {expected_json_path}")
        else:
            print(f"✗ Failed to create expected output for {pdf_path.name}")


def main():
    parser = argparse.ArgumentParser(description="Generate expected JSON outputs for sample PDFs")
    parser.add_argument("--force", action="store_true", help="Overwrite existing expected outputs")
    args = parser.parse_args()
    
    generate_expected_outputs(args.force)


if __name__ == "__main__":
    main() 