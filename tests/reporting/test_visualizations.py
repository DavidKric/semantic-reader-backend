"""
Tests for the document visualization module.

This module tests the visualization functions for document components.
"""

import pytest
import re
import base64
from app.reporting.visualizations import (
    create_layout_visualization,
    create_text_visualization,
    create_table_visualization,
    create_figure_visualization
)


@pytest.fixture
def sample_page():
    """Sample page data for testing visualizations."""
    return {
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


@pytest.fixture
def sample_table():
    """Sample table data for testing table visualization."""
    return {
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


@pytest.fixture
def sample_figure():
    """Sample figure data for testing figure visualization."""
    return {
        "x0": 100,
        "y0": 450,
        "x1": 300,
        "y1": 550,
        "type": "image",
        "caption": "Sample figure caption"
    }


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
    except Exception:
        return False


def test_create_layout_visualization(sample_page):
    """Test creating a layout visualization."""
    # Generate the visualization
    visualization = create_layout_visualization(sample_page)
    
    # Check that it's a valid base64-encoded PNG image
    assert is_valid_base64_image(visualization)


def test_create_text_visualization(sample_page):
    """Test creating a text visualization."""
    # Generate the visualization
    visualization = create_text_visualization(sample_page)
    
    # Check that it's a valid base64-encoded PNG image
    assert is_valid_base64_image(visualization)


def test_create_table_visualization(sample_table):
    """Test creating a table visualization."""
    # Generate the visualization
    visualization = create_table_visualization(sample_table)
    
    # Check that it's a valid base64-encoded PNG image
    assert is_valid_base64_image(visualization)


def test_create_figure_visualization(sample_figure):
    """Test creating a figure visualization."""
    # Generate the visualization
    visualization = create_figure_visualization(sample_figure)
    
    # Check that it's a valid base64-encoded PNG image
    assert is_valid_base64_image(visualization)


def test_empty_table_visualization():
    """Test creating a visualization for an empty table."""
    empty_table = {
        "x0": 100,
        "y0": 300,
        "x1": 500,
        "y1": 400,
        "rows": 0,
        "cols": 0,
        "cells": []
    }
    
    # Generate the visualization
    visualization = create_table_visualization(empty_table)
    
    # Should still return a valid image
    assert is_valid_base64_image(visualization)


def test_table_with_missing_properties():
    """Test creating a visualization for a table with missing properties."""
    incomplete_table = {
        "x0": 100,
        "y0": 300
        # Missing x1, y1, rows, cols, cells
    }
    
    # Generate the visualization
    visualization = create_table_visualization(incomplete_table)
    
    # Should still return a valid image
    assert is_valid_base64_image(visualization)


def test_figure_with_complex_caption(sample_figure):
    """Test creating a visualization for a figure with a complex caption structure."""
    # Copy the sample figure and modify the caption
    figure_with_complex_caption = sample_figure.copy()
    figure_with_complex_caption["caption"] = {
        "text": "Caption with object structure",
        "x0": 100,
        "y0": 560,
        "x1": 300,
        "y1": 580
    }
    
    # Generate the visualization
    visualization = create_figure_visualization(figure_with_complex_caption)
    
    # Should still return a valid image
    assert is_valid_base64_image(visualization) 