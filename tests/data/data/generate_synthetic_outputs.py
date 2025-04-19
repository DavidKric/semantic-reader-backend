#!/usr/bin/env python
"""
Script to generate synthetic JSON outputs for sample PDFs.

This script creates synthetic JSON outputs for the sample PDFs,
which can be used for testing when the actual document processing
is not available or when we need controlled test data.
"""

import argparse
import json
import random
from pathlib import Path

# Define paths
DATA_DIR = Path(__file__).parent
EXPECTED_DIR = DATA_DIR / "expected"

# Ensure expected directory exists
EXPECTED_DIR.mkdir(exist_ok=True, parents=True)


def create_synthetic_text_block(x0, y0, width, height, text):
    """
    Create a synthetic text block.
    
    Args:
        x0: Left coordinate
        y0: Bottom coordinate
        width: Block width
        height: Block height
        text: Block text
        
    Returns:
        dict: The text block
    """
    return {
        "x0": x0,
        "y0": y0,
        "x1": x0 + width,
        "y1": y0 + height,
        "text": text,
        "font": "Arial",
        "font_size": 12.0,
        "confidence": 0.99
    }


def create_synthetic_table(x0, y0, width, height, rows, cols):
    """
    Create a synthetic table.
    
    Args:
        x0: Left coordinate
        y0: Bottom coordinate
        width: Table width
        height: Table height
        rows: Number of rows
        cols: Number of columns
        
    Returns:
        dict: The table
    """
    cell_width = width / cols
    cell_height = height / rows
    
    cells = []
    for row in range(rows):
        for col in range(cols):
            cell_x0 = x0 + col * cell_width
            cell_y0 = y0 + row * cell_height
            
            cell = {
                "row": row,
                "col": col,
                "x0": cell_x0,
                "y0": cell_y0,
                "x1": cell_x0 + cell_width,
                "y1": cell_y0 + cell_height,
                "text": f"Cell R{row}C{col}"
            }
            cells.append(cell)
    
    return {
        "x0": x0,
        "y0": y0,
        "x1": x0 + width,
        "y1": y0 + height,
        "rows": rows,
        "cols": cols,
        "cells": cells
    }


def create_synthetic_figure(x0, y0, width, height, caption):
    """
    Create a synthetic figure.
    
    Args:
        x0: Left coordinate
        y0: Bottom coordinate
        width: Figure width
        height: Figure height
        caption: Figure caption
        
    Returns:
        dict: The figure
    """
    return {
        "x0": x0,
        "y0": y0,
        "x1": x0 + width,
        "y1": y0 + height,
        "caption": caption,
        "image_type": "bitmap",
        "dpi": 300
    }


def create_synthetic_page(width, height, num_blocks=10, has_tables=False, has_figures=False):
    """
    Create a synthetic page.
    
    Args:
        width: Page width
        height: Page height
        num_blocks: Number of text blocks
        has_tables: Whether to include tables
        has_figures: Whether to include figures
        
    Returns:
        dict: The page
    """
    margin = 50
    content_width = width - 2 * margin
    content_height = height - 2 * margin
    
    # Create text blocks
    blocks = []
    for i in range(num_blocks):
        block_width = random.uniform(100, 300)
        block_height = random.uniform(20, 40)
        
        # Position the block - either in a grid or randomly
        if i < 6:  # Place first blocks in a grid (2 columns x 3 rows)
            col = i % 2
            row = i // 2
            x0 = margin + col * (content_width / 2)
            y0 = margin + row * (content_height / 3)
        else:  # Place remaining blocks randomly
            x0 = random.uniform(margin, width - margin - block_width)
            y0 = random.uniform(margin, height - margin - block_height)
        
        block = create_synthetic_text_block(
            x0, y0, block_width, block_height,
            f"This is text block {i+1}. It contains sample text for testing."
        )
        blocks.append(block)
    
    # Create tables
    tables = []
    if has_tables:
        for i in range(2):  # Add 2 tables
            table_width = random.uniform(300, 400)
            table_height = random.uniform(150, 250)
            x0 = margin + random.uniform(0, content_width - table_width)
            y0 = margin + random.uniform(0, content_height - table_height)
            
            rows = random.randint(3, 6)
            cols = random.randint(3, 5)
            
            table = create_synthetic_table(x0, y0, table_width, table_height, rows, cols)
            tables.append(table)
    
    # Create figures
    figures = []
    if has_figures:
        for i in range(2):  # Add 2 figures
            figure_width = random.uniform(200, 350)
            figure_height = random.uniform(150, 250)
            x0 = margin + random.uniform(0, content_width - figure_width)
            y0 = margin + random.uniform(0, content_height - figure_height)
            
            caption = f"Figure {i+1}: Sample figure caption for testing."
            
            figure = create_synthetic_figure(x0, y0, figure_width, figure_height, caption)
            figures.append(figure)
    
    return {
        "width": width,
        "height": height,
        "number": 1,
        "blocks": blocks,
        "tables": tables,
        "figures": figures
    }


def create_synthetic_document(pdf_name, num_pages=1, has_tables=False, has_figures=False):
    """
    Create a synthetic document.
    
    Args:
        pdf_name: Name of the PDF (for metadata)
        num_pages: Number of pages
        has_tables: Whether to include tables
        has_figures: Whether to include figures
        
    Returns:
        dict: The document
    """
    # Standard page dimensions (8.5 x 11 inches at 72 DPI)
    width = 612
    height = 792
    
    # Create pages
    pages = []
    for i in range(num_pages):
        # Vary the number of blocks per page
        num_blocks = random.randint(8, 15)
        
        page = create_synthetic_page(
            width, height, num_blocks,
            has_tables=has_tables,
            has_figures=has_figures
        )
        page["number"] = i + 1
        pages.append(page)
    
    # Create metadata
    metadata = {
        "title": pdf_name.replace(".pdf", "").replace("_", " ").title(),
        "author": "Test Author",
        "creator": "PDF Test Generator",
        "producer": "Python Test Script",
        "subject": "Test Document",
        "keywords": ["test", "pdf", "synthetic"],
        "created": "2023-06-15T12:00:00Z",
        "modified": "2023-06-15T12:00:00Z",
        "pages": num_pages
    }
    
    # Create the document
    document = {
        "pages": pages,
        "metadata": metadata,
        "version": "1.0.0"
    }
    
    return document


def generate_synthetic_outputs(force=False):
    """
    Generate synthetic JSON outputs for sample PDFs.
    
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
    
    # Define characteristics for each sample type
    characteristics = {
        "sample1_simple.pdf": {"num_pages": 1, "has_tables": False, "has_figures": False},
        "sample2_multicolumn.pdf": {"num_pages": 3, "has_tables": False, "has_figures": False},
        "sample3_scanned.pdf": {"num_pages": 2, "has_tables": False, "has_figures": False},
        "sample4_tables.pdf": {"num_pages": 2, "has_tables": True, "has_figures": False},
        "sample5_figures.pdf": {"num_pages": 2, "has_tables": False, "has_figures": True},
        "sample6_mixed.pdf": {"num_pages": 3, "has_tables": True, "has_figures": True}
    }
    
    for pdf_path in pdf_files:
        expected_json_path = EXPECTED_DIR / f"{pdf_path.stem}.json"
        
        # Skip if the expected output already exists and force is False
        if expected_json_path.exists() and not force:
            print(f"Skipping {pdf_path.name} - expected output already exists. Use --force to overwrite.")
            continue
        
        # Get characteristics for this PDF type
        params = characteristics.get(pdf_path.name, {
            "num_pages": 1,
            "has_tables": False,
            "has_figures": False
        })
        
        # Create synthetic document
        result = create_synthetic_document(pdf_path.name, **params)
        
        # Save the result as the expected output
        with open(expected_json_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"✓ Created synthetic output: {expected_json_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic JSON outputs for sample PDFs")
    parser.add_argument("--force", action="store_true", help="Overwrite existing expected outputs")
    args = parser.parse_args()
    
    generate_synthetic_outputs(args.force)


if __name__ == "__main__":
    main() 