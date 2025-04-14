"""
Pytest configuration file for PaperMage-Docling tests.

This file configures pytest for testing, including HTML report generation,
custom markers, and global test fixtures.
"""

import os
import json
import pytest
import logging
from pathlib import Path
from datetime import datetime

# Get the test configuration file
CONFIG_FILE = Path(__file__).parent / "e2e_test_config.json"

def pytest_configure(config):
    """
    Configure pytest with custom markers and settings.
    """
    # Register custom markers
    config.addinivalue_line("markers", "simple: mark a test as using simple documents")
    config.addinivalue_line("markers", "complex: mark a test as using complex documents")
    config.addinivalue_line("markers", "rtl: mark a test as using RTL documents")
    config.addinivalue_line("markers", "large: mark a test as using large documents")
    config.addinivalue_line("markers", "performance: mark a test as a performance test")
    
    # Load test configuration
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            test_config = json.load(f)
            
        # Setup HTML reporting if enabled
        if test_config.get("html_report", {}).get("enabled", False):
            html_output_dir = Path(test_config["html_report"].get("output_dir", "test_results/html"))
            
            # Ensure the output directory exists
            os.makedirs(html_output_dir, exist_ok=True)
            
            # Generate timestamped report name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = html_output_dir / f"e2e_test_report_{timestamp}.html"
            
            # Add HTML reporting options to pytest configuration
            if hasattr(config, 'option'):
                config.option.htmlpath = str(report_path)
                config.option.self_contained_html = True

def pytest_html_report_title(report):
    """
    Customize the HTML report title.
    """
    report.title = "PaperMage-Docling End-to-End Test Report"

def pytest_html_results_summary(prefix, summary, postfix):
    """
    Add custom summary information to the HTML report.
    """
    prefix.extend([
        "<p>End-to-end comparison tests between PaperMage-Docling and original PaperMage</p>",
        "<p>Test environment:</p>",
        "<ul>",
        f"<li>Python version: {pytest.__version__}</li>",
        f"<li>Test run date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>",
        "</ul>",
    ])

@pytest.fixture(scope="session")
def test_config():
    """
    Load and provide the test configuration from e2e_test_config.json.
    
    Returns:
        dict: The test configuration
    """
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        # Return default configuration if file doesn't exist
        return {
            "tolerances": {
                "coordinate": 2.0,
                "text": 0.95,
                "confidence": 0.05
            },
            "test_data_paths": {
                "simple": "test_data/documents/simple",
                "complex": "test_data/documents/complex",
                "rtl": "test_data/documents/rtl",
                "large": "test_data/documents/large"
            },
            "html_report": {
                "enabled": True,
                "output_dir": "test_results/html"
            }
        }

@pytest.fixture(scope="session")
def setup_test_environment():
    """
    Set up the test environment, including setting environment variables
    and initializing necessary resources.
    
    Returns:
        dict: Test environment information
    """
    # Store original environment variables
    original_env = {}
    for key in ['PAPERMAGE_CACHE_DIR', 'PAPERMAGE_DOCLING_CACHE_DIR']:
        original_env[key] = os.environ.get(key)
    
    # Set up testing environment variables
    os.environ['PAPERMAGE_CACHE_DIR'] = str(Path(__file__).parent / "test_data" / "cache" / "papermage")
    os.environ['PAPERMAGE_DOCLING_CACHE_DIR'] = str(Path(__file__).parent / "test_data" / "cache" / "papermage_docling")
    
    # Create cache directories
    Path(os.environ['PAPERMAGE_CACHE_DIR']).mkdir(parents=True, exist_ok=True)
    Path(os.environ['PAPERMAGE_DOCLING_CACHE_DIR']).mkdir(parents=True, exist_ok=True)
    
    # Return test environment info
    yield {
        "cache_dir_papermage": os.environ['PAPERMAGE_CACHE_DIR'],
        "cache_dir_papermage_docling": os.environ['PAPERMAGE_DOCLING_CACHE_DIR'],
    }
    
    # Cleanup and restore environment variables
    for key, value in original_env.items():
        if value is None:
            if key in os.environ:
                del os.environ[key]
        else:
            os.environ[key] = value 