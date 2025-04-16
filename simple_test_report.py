"""
Simple test script for the HTML report generator.

This script tests the HTMLReportGenerator directly without using pytest.
"""

import os
import sys
from pathlib import Path
import tempfile

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

# Import the HTML generator
from app.reporting.html_generator import HTMLReportGenerator


def main():
    """Run a simple test of the HTML generator."""
    print("Testing HTML report generator...")
    
    # Create a sample document
    sample_document = {
        "id": "test123",
        "filename": "test_document.pdf",
        "metadata": {
            "title": "Test Document",
            "author": "Test Author",
            "creation_date": "2023-01-01",
            "page_count": 2,
            "language": "en"
        },
        "pages": [
            {
                "width": 612,
                "height": 792,
                "text_blocks": [
                    {
                        "x0": 100,
                        "y0": 100,
                        "x1": 400,
                        "y1": 150,
                        "text": "This is a test document."
                    },
                    {
                        "x0": 100,
                        "y0": 200,
                        "x1": 400,
                        "y1": 250,
                        "text": "It has multiple blocks of text."
                    }
                ],
                "tables": [
                    {
                        "x0": 100,
                        "y0": 300,
                        "x1": 500,
                        "y1": 400,
                        "rows": 2,
                        "cols": 2,
                        "cells": [
                            {"row": 0, "col": 0, "x0": 100, "y0": 300, "x1": 300, "y1": 350, "text": "Cell 1"},
                            {"row": 0, "col": 1, "x0": 300, "y0": 300, "x1": 500, "y1": 350, "text": "Cell 2"},
                            {"row": 1, "col": 0, "x0": 100, "y0": 350, "x1": 300, "y1": 400, "text": "Cell 3"},
                            {"row": 1, "col": 1, "x0": 300, "y0": 350, "x1": 500, "y1": 400, "text": "Cell 4"}
                        ]
                    }
                ],
                "figures": [
                    {
                        "x0": 100,
                        "y0": 450,
                        "x1": 300,
                        "y1": 550,
                        "type": "image",
                        "caption": "Sample figure caption"
                    }
                ]
            },
            {
                "width": 612,
                "height": 792,
                "text_blocks": [
                    {
                        "x0": 100,
                        "y0": 100,
                        "x1": 400,
                        "y1": 150,
                        "text": "This is page 2."
                    }
                ],
                "tables": [],
                "figures": []
            }
        ]
    }
    
    # Create a temporary output directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Created temporary directory: {temp_dir}")
        
        # Initialize the HTML generator
        generator = HTMLReportGenerator(output_dir=temp_dir)
        
        # Generate a report
        report = generator.generate_report(sample_document)
        
        # Check that the report is a string
        print(f"Generated report of length: {len(report)} characters")
        
        # Check that the report file was created
        report_path = Path(temp_dir) / f"report_{sample_document['id']}.html"
        if report_path.exists():
            print(f"Report file created: {report_path}")
            print(f"File size: {report_path.stat().st_size} bytes")
        else:
            print("Error: Report file was not created")
        
        # Check report content
        print("Checking report content...")
        if "<title>Test Document - Document Analysis Report</title>" in report:
            print("✓ Title is correct")
        else:
            print("✗ Title is incorrect")
            
        if "<h1>Test Document</h1>" in report:
            print("✓ Header is correct")
        else:
            print("✗ Header is incorrect")
            
        # Check sections
        if "<section class='metadata-section'>" in report:
            print("✓ Metadata section exists")
        else:
            print("✗ Metadata section is missing")
            
        if "<section class='overview-section'>" in report:
            print("✓ Overview section exists")
        else:
            print("✗ Overview section is missing")
            
        if "<section class='pages-section'>" in report:
            print("✓ Pages section exists")
        else:
            print("✗ Pages section is missing")
        
        print("Test completed successfully!")


if __name__ == "__main__":
    main() 