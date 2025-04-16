"""
Simple test script for the document visualization module.

This script tests the visualization functions directly without using pytest.
"""

import os
import sys
from pathlib import Path
import base64

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

# Import the visualization functions
from app.reporting.visualizations import (
    create_layout_visualization,
    create_text_visualization,
    create_table_visualization,
    create_figure_visualization
)


def is_valid_base64_image(image_data):
    """Check if the string is a valid base64-encoded image."""
    # Check if it starts with the data URI scheme
    if not image_data.startswith("data:image/png;base64,"):
        return False
    
    # Extract the base64 data
    base64_data = image_data.split(",")[1]
    
    try:
        # Try to decode the base64 data
        decoded_data = base64.b64decode(base64_data)
        
        # Check if it starts with PNG signature (89 50 4E 47 0D 0A 1A 0A)
        return decoded_data.startswith(b"\x89PNG\r\n\x1a\n")
    except Exception as e:
        print(f"Error checking base64 image: {e}")
        return False


def test_visualizations():
    """Test the visualization functions."""
    print("Testing visualization functions...")
    
    # Create a sample page
    sample_page = {
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
    }
    
    # Create a sample table
    sample_table = {
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
    
    # Create a sample figure
    sample_figure = {
        "x0": 100,
        "y0": 450,
        "x1": 300,
        "y1": 550,
        "type": "image",
        "caption": "Sample figure caption"
    }
    
    # Test layout visualization
    print("\nTesting layout visualization...")
    layout_viz = create_layout_visualization(sample_page)
    if is_valid_base64_image(layout_viz):
        print("✓ Layout visualization is valid")
    else:
        print("✗ Layout visualization is invalid")
    
    # Test text visualization
    print("\nTesting text visualization...")
    text_viz = create_text_visualization(sample_page)
    if is_valid_base64_image(text_viz):
        print("✓ Text visualization is valid")
    else:
        print("✗ Text visualization is invalid")
    
    # Test table visualization
    print("\nTesting table visualization...")
    table_viz = create_table_visualization(sample_table)
    if is_valid_base64_image(table_viz):
        print("✓ Table visualization is valid")
    else:
        print("✗ Table visualization is invalid")
    
    # Test figure visualization
    print("\nTesting figure visualization...")
    figure_viz = create_figure_visualization(sample_figure)
    if is_valid_base64_image(figure_viz):
        print("✓ Figure visualization is valid")
    else:
        print("✗ Figure visualization is invalid")
    
    # Test empty table visualization
    print("\nTesting empty table visualization...")
    empty_table = {
        "x0": 100,
        "y0": 300,
        "x1": 500,
        "y1": 400,
        "rows": 0,
        "cols": 0,
        "cells": []
    }
    empty_table_viz = create_table_visualization(empty_table)
    if is_valid_base64_image(empty_table_viz):
        print("✓ Empty table visualization is valid")
    else:
        print("✗ Empty table visualization is invalid")
    
    # Test incomplete table visualization
    print("\nTesting incomplete table visualization...")
    incomplete_table = {
        "x0": 100,
        "y0": 300
        # Missing x1, y1, rows, cols, cells
    }
    incomplete_table_viz = create_table_visualization(incomplete_table)
    if is_valid_base64_image(incomplete_table_viz):
        print("✓ Incomplete table visualization is valid")
    else:
        print("✗ Incomplete table visualization is invalid")
    
    # Test complex caption figure visualization
    print("\nTesting figure with complex caption...")
    figure_with_complex_caption = sample_figure.copy()
    figure_with_complex_caption["caption"] = {
        "text": "Caption with object structure",
        "x0": 100,
        "y0": 560,
        "x1": 300,
        "y1": 580
    }
    complex_caption_viz = create_figure_visualization(figure_with_complex_caption)
    if is_valid_base64_image(complex_caption_viz):
        print("✓ Complex caption figure visualization is valid")
    else:
        print("✗ Complex caption figure visualization is invalid")
    
    print("\nAll visualization tests completed!")


if __name__ == "__main__":
    test_visualizations() 