"""
Tests for the HTML report generator module.

This module tests the functionality of the HTML report generation component,
ensuring that it correctly converts document processing results into HTML reports.
"""

import os
import pytest
from pathlib import Path
import tempfile
import re
from bs4 import BeautifulSoup

from app.reporting.html_generator import HTMLReportGenerator


@pytest.fixture
def sample_document_result():
    """Sample document processing result for testing."""
    return {
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


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


def test_html_generator_init(temp_output_dir):
    """Test HTML generator initialization."""
    # Test with output directory
    generator = HTMLReportGenerator(output_dir=temp_output_dir)
    assert generator.output_dir == Path(temp_output_dir)
    
    # Test default CSS and JS files are created
    css_file = Path(temp_output_dir) / "templates" / "report.css"
    js_file = Path(temp_output_dir) / "templates" / "report.js"
    assert Path(generator.output_dir).exists()
    
    # Test without output directory
    generator = HTMLReportGenerator()
    assert generator.output_dir is None


def test_generate_report(sample_document_result, temp_output_dir):
    """Test generating an HTML report."""
    generator = HTMLReportGenerator(output_dir=temp_output_dir)
    report = generator.generate_report(sample_document_result)
    
    # Check that the report is a string
    assert isinstance(report, str)
    
    # Parse the report with BeautifulSoup for structure checking
    soup = BeautifulSoup(report, 'html.parser')
    
    # Check basic document structure
    assert soup.title.text == "Test Document - Document Analysis Report"
    assert soup.find("h1").text == "Test Document"
    
    # Check that metadata is included
    metadata_section = soup.find("section", class_="metadata-section")
    assert metadata_section is not None
    metadata_table = metadata_section.find("table", class_="metadata-table")
    assert "Author" in metadata_table.text
    assert "Test Author" in metadata_table.text
    
    # Check overview section
    overview_section = soup.find("section", class_="overview-section")
    assert overview_section is not None
    stats = overview_section.find_all("div", class_="stat-card")
    assert len(stats) == 4  # Pages, Text Blocks, Tables, Figures
    
    # Check that both pages are included
    pages_section = soup.find("section", class_="pages-section")
    assert pages_section is not None
    page_nav_buttons = pages_section.find_all("button", class_="page-nav-btn")
    assert len(page_nav_buttons) == 2  # Two pages
    
    # Check visualization tabs
    tabs = soup.find_all("div", class_="visualization-tabs")
    assert len(tabs) == 2  # One for each page
    tab_buttons = tabs[0].find_all("button", class_="tab-btn")
    assert len(tab_buttons) == 4  # Layout, Text, Tables, Figures
    
    # Check that the report file was created
    report_file = Path(temp_output_dir) / f"report_{sample_document_result['id']}.html"
    assert report_file.exists()
    assert report_file.stat().st_size > 0


def test_generate_report_without_output_dir(sample_document_result):
    """Test generating an HTML report without saving to disk."""
    generator = HTMLReportGenerator(output_dir=None)
    report = generator.generate_report(sample_document_result)
    
    # Check that the report is a string
    assert isinstance(report, str)
    
    # Parse the report with BeautifulSoup for structure checking
    soup = BeautifulSoup(report, 'html.parser')
    
    # Check basic document structure
    assert soup.title.text == "Test Document - Document Analysis Report"


def test_generate_report_custom_title(sample_document_result, temp_output_dir):
    """Test generating an HTML report with a custom title."""
    generator = HTMLReportGenerator(output_dir=temp_output_dir)
    report = generator.generate_report(sample_document_result, title="Custom Title")
    
    # Parse the report with BeautifulSoup for structure checking
    soup = BeautifulSoup(report, 'html.parser')
    
    # Check title
    assert soup.title.text == "Custom Title - Document Analysis Report"
    assert soup.find("h1").text == "Custom Title"


def test_page_visualization_generation(sample_document_result, temp_output_dir):
    """Test that visualizations for pages are generated correctly."""
    generator = HTMLReportGenerator(output_dir=temp_output_dir)
    report = generator.generate_report(sample_document_result)
    
    # Parse the report with BeautifulSoup
    soup = BeautifulSoup(report, 'html.parser')
    
    # Check page containers
    page_containers = soup.find_all("div", class_="page-container")
    assert len(page_containers) == 2
    
    # Check page 1 visualizations
    page1 = page_containers[0]
    assert "Page 1" in page1.find("h3").text
    
    # Check tab content for page 1
    tab_content = page1.find("div", class_="tab-content")
    tab_panes = tab_content.find_all("div", class_="tab-pane")
    assert len(tab_panes) == 4  # Layout, Text, Tables, Figures
    
    # Check layout tab (active by default)
    layout_tab = tab_panes[0]
    assert "active" in layout_tab["class"]
    assert layout_tab.find("div", class_="layout-visualization") is not None
    
    # Check text blocks visualization
    text_blocks = layout_tab.find_all("div", class_="text-block")
    assert len(text_blocks) == 2  # Two text blocks on page 1
    
    # Check table visualization
    table_blocks = layout_tab.find_all("div", class_="table-block")
    assert len(table_blocks) == 1  # One table on page 1
    
    # Check figure visualization
    figure_blocks = layout_tab.find_all("div", class_="figure-block")
    assert len(figure_blocks) == 1  # One figure on page 1


def test_empty_elements(temp_output_dir):
    """Test generating a report with empty elements."""
    # Create a document with no text blocks, tables, or figures
    empty_document = {
        "id": "empty123",
        "filename": "empty_document.pdf",
        "metadata": {
            "title": "Empty Document",
        },
        "pages": [
            {
                "width": 612,
                "height": 792,
                "text_blocks": [],
                "tables": [],
                "figures": []
            }
        ]
    }
    
    generator = HTMLReportGenerator(output_dir=temp_output_dir)
    report = generator.generate_report(empty_document)
    
    # Parse the report with BeautifulSoup
    soup = BeautifulSoup(report, 'html.parser')
    
    # Check overview section stats
    overview_section = soup.find("section", class_="overview-section")
    stats = overview_section.find_all("div", class_="stat-value")
    assert stats[0].text == "1"  # 1 page
    assert stats[1].text == "0"  # 0 text blocks
    assert stats[2].text == "0"  # 0 tables
    assert stats[3].text == "0"  # 0 figures


def test_javascript_inclusion(sample_document_result, temp_output_dir):
    """Test that JavaScript is included in the report."""
    # Test with interactive elements
    generator = HTMLReportGenerator(output_dir=temp_output_dir)
    report_with_js = generator.generate_report(sample_document_result, include_interactive=True)
    assert "<script>" in report_with_js
    assert "function showPage" in report_with_js
    
    # Test without interactive elements
    report_without_js = generator.generate_report(sample_document_result, include_interactive=False)
    assert not ("<script>" in report_without_js and "function showPage" in report_without_js) 