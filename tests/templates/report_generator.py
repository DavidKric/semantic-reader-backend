"""
Utility for generating HTML reports for document visualizations.

This module provides functions for:
1. Rendering templates with Jinja2
2. Generating document visualization reports
3. Integrating with pytest-html reports
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

# Import the report schema
from tests.schemas.visualization_report_schema import (
    PageVisualization,
    VisualizationReport,
    get_entity_counts,
    format_json_preview
)

# Get the root of the test directory for reference
TEST_DIR = Path(__file__).parent.parent
TEMPLATE_DIR = TEST_DIR / "templates"
OUTPUT_DIR = TEST_DIR / "test_outputs" / "reports"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Try to use Jinja2 for templating
try:
    import jinja2
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    print("Warning: Jinja2 not available. HTML reports will not be generated.")


def render_template(template_name: str, context: Dict[str, Any]) -> str:
    """
    Render a template with the given context.
    
    Args:
        template_name: Name of the template file
        context: Variables to pass to the template
    
    Returns:
        Rendered template as a string
    """
    if not JINJA2_AVAILABLE:
        return f"Template '{template_name}' could not be rendered (Jinja2 not available)"
    
    # Set up Jinja2 environment
    template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATE_DIR)
    template_env = jinja2.Environment(loader=template_loader)
    
    # Get the template
    template = template_env.get_template(template_name)
    
    # Render the template
    return template.render(**context)


def generate_visualization_report(
    pdf_path: Path,
    papermage_doc: Dict[str, Any],
    visualization_paths: Dict[str, Dict[int, str]],
    output_dir: Optional[Path] = None
) -> str:
    """
    Generate a visualization report for a document.
    
    Args:
        pdf_path: Path to the original PDF
        papermage_doc: Document data structure
        visualization_paths: Dictionary mapping granularity levels to page paths
            e.g., {'word': {1: '/path/to/word_page1.png', 2: '/path/to/word_page2.png'}}
        output_dir: Directory to save the report
    
    Returns:
        Path to the generated report
    """
    if not JINJA2_AVAILABLE:
        print("Warning: Cannot generate report without Jinja2")
        return ""
    
    # Use specified output directory or default
    if output_dir is None:
        output_dir = OUTPUT_DIR
    
    # Create the report structure
    report = VisualizationReport(
        document_name=pdf_path.name,
        page_count=len(papermage_doc.get("pages", [])),
        entity_counts=get_entity_counts(papermage_doc),
        json_structure=format_json_preview(papermage_doc)
    )
    
    # Add page visualizations
    for page_idx in range(report.page_count):
        page_num = page_idx + 1
        
        # Create page visualization entry
        page_vis = PageVisualization(number=page_num)
        
        # Add visualization paths for each granularity level
        for level_type in ["original", "char", "word", "line"]:
            if level_type in visualization_paths and page_num in visualization_paths[level_type]:
                setattr(page_vis, level_type, visualization_paths[level_type][page_num])
        
        # Add entity preview if available
        if page_idx < len(papermage_doc.get("pages", [])):
            page_data = papermage_doc["pages"][page_idx]
            page_vis.entity_preview = format_json_preview(page_data, max_length=500)
        
        report.pages.append(page_vis)
    
    # Generate the output filename
    output_filename = f"{pdf_path.stem}_visualization_report.html"
    output_path = output_dir / output_filename
    
    # Render the template
    rendered_html = render_template(
        "visualization_report_template.html", 
        report.to_template_vars()
    )
    
    # Write the report to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    
    # Save the output path to the report
    report.output_path = str(output_path)
    
    return str(output_path)


def copy_report_assets_to_pytest_html(
    report_path: str, 
    visualization_paths: Dict[str, Dict[int, str]],
    pytest_html_dir: Optional[str] = None
) -> bool:
    """
    Copy report assets to pytest-html output directory.
    
    Args:
        report_path: Path to the generated report
        visualization_paths: Dictionary of visualization paths
        pytest_html_dir: Directory of pytest-html output (auto-detected if None)
    
    Returns:
        True if successful, False otherwise
    """
    # If no pytest-html directory provided, try to find it
    if pytest_html_dir is None:
        # Look for test_results/html directory
        default_html_dir = Path(__file__).parent.parent.parent / "test_results" / "html"
        
        # Try to find most recent HTML report
        if default_html_dir.exists():
            html_files = list(default_html_dir.glob("*.html"))
            if html_files:
                # Sort by modification time (newest first)
                html_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                pytest_html_dir = str(html_files[0].parent)
    
    if not pytest_html_dir or not os.path.exists(pytest_html_dir):
        print("Warning: pytest-html directory not found")
        return False
    
    try:
        # Create assets directory if it doesn't exist
        assets_dir = Path(pytest_html_dir) / "assets"
        assets_dir.mkdir(exist_ok=True)
        
        # Copy the report
        report_filename = os.path.basename(report_path)
        shutil.copy2(report_path, os.path.join(pytest_html_dir, report_filename))
        
        # Copy visualization images
        for level_type, pages in visualization_paths.items():
            for page_num, vis_path in pages.items():
                if os.path.exists(vis_path):
                    dest_filename = os.path.basename(vis_path)
                    shutil.copy2(vis_path, os.path.join(assets_dir, dest_filename))
        
        return True
    except Exception as e:
        print(f"Error copying assets to pytest-html directory: {e}")
        return False


def attach_report_to_pytest(report_path: str, request) -> bool:
    """
    Attach report to pytest as an extra attachment.
    
    Args:
        report_path: Path to the report
        request: pytest request object
    
    Returns:
        True if successful, False otherwise
    """
    try:
        from pytest_html import extras
        
        if hasattr(request, "node") and hasattr(request.node, "user_properties"):
            # Add the report to the HTML attachment extras
            request.node.user_properties.append(
                ("extra", extras.html(report_path))
            )
            return True
    except ImportError:
        print("Warning: pytest-html not available for report attachment")
    except Exception as e:
        print(f"Error attaching report to pytest: {e}")
    
    return False 