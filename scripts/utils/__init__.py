"""
Utility scripts for the papermage-docling project.

This module initializes the scripts/utils directory as a Python package
and provides helper functions for scripts to properly import from the src directory.
"""

import os
import sys
from pathlib import Path


def add_src_to_path():
    """Add the src directory to Python path to enable imports from the package."""
    # Get the project root directory (2 levels up from this file)
    project_root = Path(__file__).parent.parent.parent.absolute()
    src_path = os.path.join(project_root, "src")
    
    # Add to path if not already there
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    return project_root, src_path 