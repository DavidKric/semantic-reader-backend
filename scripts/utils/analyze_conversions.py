#!/usr/bin/env python3
"""
Run document conversion analysis and generate a report.

This script analyzes the codebase to identify all conversion points between
Docling's native document structures and PaperMage's format, and generates
a comprehensive report to guide the refactoring process.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Add the proper import path handling
from . import add_src_to_path
project_root, _ = add_src_to_path()

from papermage_docling.analysis.document_conversion_map import create_conversion_map


def main():
    """Run the document conversion analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze document format conversions in the codebase"
    )
    parser.add_argument(
        "--output",
        default="docs/conversion_map.json",
        help="Output file for the report (default: docs/conversion_map.json)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger("conversion-analysis")

    # Ensure output directory exists
    output_path = Path(args.output)
    os.makedirs(output_path.parent, exist_ok=True)

    logger.info(f"Starting document conversion analysis...")
    report = create_conversion_map(
        project_root=str(project_root),
        output_file=str(output_path)
    )
    
    # Print summary
    logger.info(f"Analysis complete. Found {len(report['conversion_points'])} conversion points.")
    logger.info(f"Report saved to {output_path}")
    
    # Print high impact recommendations
    if report['recommendations']['high']:
        logger.info("High impact recommendations:")
        for rec in report['recommendations']['high']:
            logger.info(f"  - {rec['module']}.{rec['function']}: {rec['recommendation']}")


if __name__ == "__main__":
    main() 