#!/usr/bin/env python3
"""
Example demonstrating the use of the PdfVisualizer from papermage_docling.

This script shows how to:
1. Initialize the PdfVisualizer
2. Visualize a PDF document with different granularity levels
3. Use different options like displaying text, showing interactively, etc.
"""

import os
import argparse
from pathlib import Path
from papermage_docling.visualizers import PdfVisualizer


def parse_args():
    """Parse command line arguments for the example."""
    parser = argparse.ArgumentParser(
        description="Example for visualizing a PDF document with papermage_docling."
    )
    
    parser.add_argument(
        "-i", "--input-pdf",
        type=str,
        required=True,
        help="Path to the PDF file to visualize"
    )
    
    parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default="./output",
        help="Directory to save visualization images (default: ./output)"
    )
    
    parser.add_argument(
        "-c", "--category",
        type=str,
        choices=["all", "char", "word", "line"],
        default="all",
        help="Cell unit to visualize (default: all)"
    )
    
    parser.add_argument(
        "-p", "--page",
        type=int,
        default=1,
        help="Page number to visualize (default: 1, use -1 for all pages)"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Show visualizations interactively (default: False)"
    )
    
    parser.add_argument(
        "--text",
        action="store_true",
        help="Display text in visualizations instead of bounding boxes (default: False)"
    )
    
    parser.add_argument(
        "--detect-rtl",
        action="store_true",
        help="Enable RTL text detection and processing (default: False)"
    )
    
    return parser.parse_args()


def main():
    """Main function for the example."""
    args = parse_args()
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
        print(f"Created output directory: {output_dir}")
    
    # Initialize the visualizer
    visualizer = PdfVisualizer(
        log_level="info",
        display_text=args.text,
        interactive=args.interactive,
        output_dir=output_dir
    )
    
    # Set Docling options
    parser_kwargs = {
        "detect_rtl": args.detect_rtl,
        "detect_tables": True,
        "detect_figures": True,
    }
    
    # Visualize the PDF
    print(f"Visualizing PDF: {args.input_pdf}")
    print(f"  Page: {args.page if args.page != -1 else 'all'}")
    print(f"  Category: {args.category}")
    print(f"  Display text: {args.text}")
    print(f"  Interactive: {args.interactive}")
    print(f"  RTL detection: {args.detect_rtl}")
    print(f"  Output directory: {output_dir}")
    print("")
    print("Using Docling's DocumentConverter for parsing...")
    
    visualizer.visualize_pdf(
        pdf_path=args.input_pdf,
        page_num=args.page,
        category=args.category,
        parser_kwargs=parser_kwargs
    )
    
    print("\nVisualization completed. Output files saved to:", output_dir)
    
    # List output files
    output_files = list(output_dir.glob(f"{os.path.basename(args.input_pdf)}.page_*.*.png"))
    if output_files:
        print("\nGenerated visualization files:")
        for file in output_files:
            print(f"  {file.name}")
    else:
        print("\nNo visualization files were generated.")


if __name__ == "__main__":
    main() 