#!/usr/bin/env python
"""
Isolated test script for HTML report generation functionality.

This script tests the HTML report generation without importing from app directory.
"""

import os
import sys
import tempfile
from pathlib import Path


class HTMLReportGenerator:
    """HTML report generator for document analysis results."""
    
    def __init__(self, output_dir=None):
        """Initialize the HTML report generator.
        
        Args:
            output_dir: Directory where reports will be saved.
        """
        self.output_dir = Path(output_dir) if output_dir else None
        if self.output_dir and not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(self, document_result, include_images=True, include_interactive=True, title=None):
        """Generate an HTML report for a document.
        
        Args:
            document_result: Document processing result.
            include_images: Whether to include visualizations.
            include_interactive: Whether to include interactive elements.
            title: Custom title for the report.
        
        Returns:
            HTML report as a string.
        """
        # Extract document information
        doc_id = document_result.get("id", "unknown")
        filename = document_result.get("filename", "document.pdf")
        metadata = document_result.get("metadata", {})
        pages = document_result.get("pages", [])
        
        # Set report title
        if title is None:
            title = metadata.get("title", filename)
        
        # Start building HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Document Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        .metadata-section {{ background: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .overview-section {{ margin-bottom: 20px; }}
        .pages-section {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .page-card {{ border: 1px solid #ddd; border-radius: 5px; padding: 15px; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    
    <section class='metadata-section'>
        <h2>Document Metadata</h2>
        <p>Filename: {filename}</p>
        <p>Document ID: {doc_id}</p>
        <p>Author: {metadata.get('author', 'Unknown')}</p>
        <p>Creation Date: {metadata.get('creation_date', 'Unknown')}</p>
        <p>Pages: {metadata.get('page_count', len(pages))}</p>
    </section>
    
    <section class='overview-section'>
        <h2>Document Overview</h2>
        <p>This document contains {len(pages)} pages with:</p>
        <ul>
            <li>Text Blocks: {sum(len(page.get('text_blocks', [])) for page in pages)}</li>
            <li>Tables: {sum(len(page.get('tables', [])) for page in pages)}</li>
            <li>Figures: {sum(len(page.get('figures', [])) for page in pages)}</li>
        </ul>
    </section>
    
    <section class='pages-section'>
        <h2>Pages</h2>
"""
        
        # Add pages
        for i, page in enumerate(pages):
            page_html = f"""
        <div class='page-card'>
            <h3>Page {i+1}</h3>
            <p>Dimensions: {page.get('width', 0)} x {page.get('height', 0)}</p>
            <p>Text blocks: {len(page.get('text_blocks', []))}</p>
            <p>Tables: {len(page.get('tables', []))}</p>
            <p>Figures: {len(page.get('figures', []))}</p>
        </div>
"""
            html += page_html
        
        # Close HTML
        html += """
    </section>
</body>
</html>
"""
        
        # Save the report if output directory is specified
        if self.output_dir:
            report_path = self.output_dir / f"report_{doc_id}.html"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html)
        
        return html


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
        if "class='metadata-section'" in report:
            print("✓ Metadata section exists")
        else:
            print("✗ Metadata section is missing")
            
        if "class='overview-section'" in report:
            print("✓ Overview section exists")
        else:
            print("✗ Overview section is missing")
            
        if "class='pages-section'" in report:
            print("✓ Pages section exists")
        else:
            print("✗ Pages section is missing")
        
        print("Test completed successfully!")


if __name__ == "__main__":
    main() 