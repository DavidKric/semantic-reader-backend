"""
Reporting module for generating HTML reports and visualizations.

This module provides functionality for generating HTML reports and
visualizations of document processing results.
"""

from app.reporting.html_generator import HTMLReportGenerator
from app.reporting.visualizations import (
    create_layout_visualization,
    create_text_visualization,
    create_table_visualization,
    create_figure_visualization
) 