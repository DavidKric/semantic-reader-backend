#!/usr/bin/env python
"""
Utility script to update expected JSON outputs for tests.

This script processes the sample PDF files and generates new expected JSON outputs,
which can be used to update the golden files for snapshot tests.
"""

import os
import json
import shutil
import argparse
from pathlib import Path

# Add parent directory to Python path to import app modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the necessary modules
# These will need to be adjusted for your specific application
try:
    from app.services.pipeline_service import PipelineService
except ImportError:
    print("Warning: Could not import PipelineService. Make sure the application is properly installed.")
    PipelineService = None

# Define paths
TEST_DIR = Path(__file__).parent
TEST_DATA_DIR = TEST_DIR / "data"
TEST_EXPECTED_DIR = TEST_DATA_DIR / "expected"

# Ensure directories exist
TEST_EXPECTED_DIR.mkdir(exist_ok=True, parents=True)

def process_pdf(pdf_path):
    """
    Process a PDF file and return the JSON output.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        dict: The JSON output from processing the PDF
    """
    if PipelineService is None:
        raise ImportError("PipelineService is not available. Cannot process PDFs.")
    
    # Create a pipeline service instance
    # This may need to be adjusted based on your application's requirements
    pipeline_service = PipelineService()
    
    try:
        # Process the document
        result = pipeline_service.process_document(str(pdf_path))
        return result
    except Exception as e:
        print(f"Error processing {pdf_path.name}: {e}")
        return None

def update_expected_outputs(force=False):
    """
    Update expected JSON outputs for all sample PDFs.
    
    Args:
        force: If True, overwrite existing expected outputs
    """
    # Find all PDF files in the test data directory
    pdf_files = list(TEST_DATA_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {TEST_DATA_DIR}")
        return
    
    print(f"Found {len(pdf_files)} PDF files.")
    
    for pdf_path in pdf_files:
        expected_json_path = TEST_EXPECTED_DIR / f"{pdf_path.stem}.json"
        
        # Skip if the expected output already exists and force is False
        if expected_json_path.exists() and not force:
            print(f"Skipping {pdf_path.name} - expected output already exists. Use --force to overwrite.")
            continue
        
        print(f"Processing {pdf_path.name}...")
        
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
    parser = argparse.ArgumentParser(description="Update expected JSON outputs for tests")
    parser.add_argument("--force", action="store_true", help="Overwrite existing expected outputs")
    args = parser.parse_args()
    
    update_expected_outputs(args.force)

if __name__ == "__main__":
    main() 