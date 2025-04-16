"""
Simple test script for the report service.

This script tests the ReportService class directly without using pytest.
"""

import os
import sys
from pathlib import Path
import tempfile
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

# Import the ReportService
from app.reporting.service import ReportService


def test_report_service():
    """Test the ReportService class."""
    print("Testing ReportService...")
    
    # Create a sample document
    sample_document = {
        "id": "test123",
        "filename": "test_document.pdf",
        "metadata": {
            "title": "Test Document",
            "author": "Test Author",
            "creation_date": "2023-01-01",
            "page_count": 2
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
                    }
                ]
            }
        ]
    }
    
    # Create a temporary output directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Created temporary directory: {temp_dir}")
        
        # Test ReportService initialization with output directory
        service = ReportService(output_dir=temp_dir)
        
        # Check initialization
        if service.output_dir == Path(temp_dir):
            print("✓ ReportService initialized correctly with output directory")
        else:
            print("✗ ReportService failed to initialize with output directory")
        
        if service.html_generator is not None:
            print("✓ HTML generator initialized correctly")
        else:
            print("✗ HTML generator failed to initialize")
        
        # Test generating a report
        report = service.generate_report(sample_document)
        
        # Check report generation
        if isinstance(report, str):
            print("✓ Report generated as string")
        else:
            print(f"✗ Report not a string (type: {type(report)})")
        
        # Check report content
        if "<title>Test Document - Document Analysis Report</title>" in report:
            print("✓ Report title is correct")
        else:
            print("✗ Report title is incorrect")
        
        if "<h1>Test Document</h1>" in report:
            print("✓ Report header is correct")
        else:
            print("✗ Report header is incorrect")
        
        # Check report file creation
        report_path = Path(temp_dir) / f"report_{sample_document['id']}.html"
        if report_path.exists():
            print(f"✓ Report file created: {report_path}")
        else:
            print("✗ Report file was not created")
        
        # Test get_report_path
        path = service.get_report_path(sample_document["id"])
        if path == report_path:
            print("✓ get_report_path returns correct path")
        else:
            print(f"✗ get_report_path returned incorrect path: {path}")
        
        # Test get_report_path with non-existent document
        nonexistent_path = service.get_report_path("nonexistent")
        if nonexistent_path is None:
            print("✓ get_report_path returns None for non-existent document")
        else:
            print(f"✗ get_report_path returned path for non-existent document: {nonexistent_path}")
    
    # Test ReportService initialization without output directory
    service = ReportService()
    
    # Check initialization
    if service.output_dir is None:
        print("✓ ReportService initialized correctly without output directory")
    else:
        print(f"✗ ReportService initialized with unexpected output directory: {service.output_dir}")
    
    # Test get_report_path with no output directory
    path = service.get_report_path(sample_document["id"])
    if path is None:
        print("✓ get_report_path returns None when no output directory is set")
    else:
        print(f"✗ get_report_path returned unexpected path: {path}")
    
    # Test custom report title
    with tempfile.TemporaryDirectory() as temp_dir:
        service = ReportService(output_dir=temp_dir)
        
        # Generate report with custom title
        report = service.generate_report(sample_document, title="Custom Report Title")
        
        # Check custom title
        if "<title>Custom Report Title - Document Analysis Report</title>" in report:
            print("✓ Custom report title applied correctly")
        else:
            print("✗ Custom report title not applied")
        
        if "<h1>Custom Report Title</h1>" in report:
            print("✓ Custom report header applied correctly")
        else:
            print("✗ Custom report header not applied")
    
    print("\nAll ReportService tests completed!")


if __name__ == "__main__":
    test_report_service() 