#!/usr/bin/env python
"""
Comparison Visualizer for Document Parsing

This module provides utilities to compare document parsing results between
PaperMage-Docling converter and direct Docling parsing. It generates visual
comparisons and statistics to help understand differences between the two
implementations.

Requirements:
- papermage_docling: For document conversion
- docling: For direct document parsing (optional)
- matplotlib: For visualization generation
- numpy: For data manipulation
- pillow: For image processing
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

# Check for visualization libraries
try:
    import matplotlib
    import matplotlib.pyplot as plt
    import numpy as np
    from PIL import Image
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

# Check for Docling availability
try:
    import docling
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

# Import the converter
try:
    from papermage_docling.converter import convert_document, docling_to_papermage
except ImportError:
    # This is expected if running directly and not as part of the package
    pass

logger = logging.getLogger(__name__)


class ComparisonVisualizer:
    """
    A class to compare document parsing results between PaperMage-Docling and direct Docling.
    
    This visualizer generates:
    1. Side-by-side comparisons of parsing results (when Docling is available)
    2. Statistics on entity detection differences
    3. Performance metrics
    
    When Docling is not available, it will still generate visualizations for PaperMage output.
    """
    
    def __init__(self, output_dir: Union[str, Path] = None, show_interactive: bool = False, 
                 detect_tables: bool = True, detect_figures: bool = True, 
                 ocr_enabled: bool = False, interactive: bool = False):
        """
        Initialize the comparison visualizer.
        
        Args:
            output_dir: Directory to save visualizations (default: current directory)
            show_interactive: Whether to show visualizations interactively (default: False)
            detect_tables: Whether to detect tables during document processing
            detect_figures: Whether to detect figures during document processing
            ocr_enabled: Whether to enable OCR for scanned documents
            interactive: Alias for show_interactive for API compatibility
        """
        if not VISUALIZATION_AVAILABLE:
            raise ImportError(
                "Visualization libraries not available. Please install: "
                "matplotlib, numpy, pillow"
            )
        
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.show_interactive = show_interactive or interactive
        self.docling_available = DOCLING_AVAILABLE
        
        # Save processing options
        self.options = {
            "detect_tables": detect_tables,
            "detect_figures": detect_figures,
            "enable_ocr": ocr_enabled
        }
        
        # Create output directory if it doesn't exist
        if not self.output_dir.exists():
            os.makedirs(self.output_dir)
            logger.info(f"Created output directory: {self.output_dir}")
        
        if not self.docling_available:
            logger.warning("Docling is not available - comparison will be limited to PaperMage output only")
    
    def visualize_pdf_comparison(self, pdf_path: Union[str, Path], output_dir: Union[str, Path] = None) -> List[Path]:
        """
        Compatibility method that calls compare_documents with the right parameters.
        This method ensures compatibility with document_comparison.py script.
        
        Args:
            pdf_path: Path to the PDF document
            output_dir: Optional output directory (overrides the one from __init__)
            
        Returns:
            List of paths to generated visualization files
        """
        # Update output directory if provided
        if output_dir:
            self.output_dir = Path(output_dir)
            if not self.output_dir.exists():
                os.makedirs(self.output_dir)
                logger.info(f"Created output directory: {self.output_dir}")
        
        # Call the main compare_documents method
        return self.compare_documents(pdf_path, self.options)
    
    def compare_documents(
        self, 
        pdf_path: Union[str, Path], 
        options: Optional[Dict[str, Any]] = None
    ) -> List[Path]:
        """
        Compare document parsing between PaperMage-Docling and direct Docling.
        If Docling is not available, only PaperMage visualizations will be generated.
        
        Args:
            pdf_path: Path to the PDF document
            options: Dictionary of options for document parsing
                - detect_tables: Whether to detect tables (default: True)
                - detect_figures: Whether to detect figures (default: True)
                - enable_ocr: Whether to enable OCR for scanned documents (default: False)
                
        Returns:
            List of paths to generated visualization files
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Default options
        if options is None:
            options = {
                "detect_tables": True,
                "detect_figures": True,
                "enable_ocr": False,
            }
        
        # Time the conversion process
        start_time = time.time()
        
        # Convert with PaperMage-Docling
        logger.info(f"Converting {pdf_path.name} with PaperMage-Docling...")
        try:
            pm_doc = convert_document(pdf_path, options)
            pm_time = time.time() - start_time
            logger.info(f"PaperMage-Docling conversion completed in {pm_time:.2f}s")
        except Exception as e:
            logger.error(f"PaperMage-Docling conversion failed: {e}")
            raise
        
        # Initialize direct_pm_doc and docling_time
        direct_pm_doc = None
        docling_time = 0
        
        # Parse with direct Docling if available
        if self.docling_available:
            logger.info(f"Parsing {pdf_path.name} with direct Docling...")
            start_time = time.time()
            try:
                docling_doc = docling.parsers.document_parser.parse_pdf(
                    pdf_path,
                    detect_tables=options.get("detect_tables", True),
                    detect_figures=options.get("detect_figures", True),
                    ocr=options.get("enable_ocr", False),
                )
                docling_time = time.time() - start_time
                logger.info(f"Direct Docling parsing completed in {docling_time:.2f}s")
                
                # Convert the direct Docling document to PaperMage format for comparison
                direct_pm_doc = docling_to_papermage(docling_doc)
            except Exception as e:
                logger.error(f"Direct Docling parsing failed: {e}")
                logger.warning("Will continue with PaperMage-only visualization")
        else:
            logger.info("Docling is not available - generating PaperMage-only visualizations")
        
        # Visualize outputs
        if direct_pm_doc:
            # If Docling output is available, do comparison
            output_paths = self._visualize_comparisons(
                pdf_path.stem, pm_doc, direct_pm_doc, pm_time, docling_time
            )
        else:
            # If only PaperMage output is available, do single visualization
            output_paths = self._visualize_papermage_only(
                pdf_path.stem, pm_doc, pm_time
            )
        
        return output_paths
    
    def _visualize_papermage_only(
        self,
        doc_name: str,
        pm_doc: Dict,
        pm_time: float
    ) -> List[Path]:
        """
        Generate visualizations for PaperMage-Docling output only.
        
        Args:
            doc_name: Name of the document
            pm_doc: Document parsed with PaperMage-Docling
            pm_time: Time taken for conversion
            
        Returns:
            List of paths to generated visualization files
        """
        output_paths = []
        
        # Plot PaperMage entity statistics
        stats_path = self._plot_papermage_stats(doc_name, pm_doc, pm_time)
        if stats_path:
            output_paths.append(stats_path)
        
        # For each page, visualize PaperMage layout
        for page_idx in range(len(pm_doc.get("pages", []))):
            page_path = self._visualize_papermage_page(doc_name, page_idx, pm_doc)
            if page_path:
                output_paths.append(page_path)
        
        return output_paths
    
    def _plot_papermage_stats(
        self,
        doc_name: str,
        pm_doc: Dict,
        pm_time: float
    ) -> Optional[Path]:
        """
        Generate statistics visualization for PaperMage-Docling only.
        
        Args:
            doc_name: Name of the document
            pm_doc: Document parsed with PaperMage-Docling
            pm_time: Time taken for conversion
            
        Returns:
            Path to the generated statistics visualization
        """
        # Count entities
        entity_counts = self._count_entities(pm_doc)
        
        # Set up the plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
        fig.suptitle(f"Document Parsing: {doc_name}", fontsize=16)
        
        # 1. Entity Count Plot
        entity_types = sorted(entity_counts.keys())
        entity_values = [entity_counts[t] for t in entity_types]
        
        bars = ax1.bar(entity_types, entity_values, color='blue')
        ax1.set_title('Entity Count')
        ax1.set_ylabel('Count')
        ax1.set_xlabel('Entity Type')
        ax1.set_xticklabels(entity_types, rotation=45, ha='right')
        
        # Add count labels on bars
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax1.annotate(f'{height}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom')
        
        # 2. Processing Time
        ax2.bar(['Processing Time'], [pm_time], color='green')
        ax2.set_title('Performance')
        ax2.set_ylabel('Time (seconds)')
        ax2.text(0, pm_time + 0.1, f"{pm_time:.2f}s", ha='center')
        
        # Save the figure
        plt.tight_layout()
        output_path = self.output_dir / f"{doc_name}_papermage_stats.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        
        if self.show_interactive:
            plt.show()
        else:
            plt.close(fig)
        
        return output_path
    
    def _visualize_papermage_page(
        self,
        doc_name: str,
        page_idx: int,
        pm_doc: Dict
    ) -> Optional[Path]:
        """
        Visualize a single page from PaperMage-Docling output.
        
        Args:
            doc_name: Name of the document
            page_idx: Index of the page to visualize
            pm_doc: Document parsed with PaperMage-Docling
            
        Returns:
            Path to the generated page visualization
        """
        # Check if page exists
        pm_pages = pm_doc.get("pages", [])
        if page_idx >= len(pm_pages):
            logger.warning(f"Page {page_idx} not found in document")
            return None
        
        pm_page = pm_pages[page_idx]
        
        # Set up the plot
        fig, ax = plt.subplots(figsize=(12, 16))
        fig.suptitle(f"Page {page_idx+1}: {doc_name}", fontsize=16)
        
        # Plot PaperMage entities
        self._plot_page_entities(ax, pm_doc, page_idx)
        
        # Save the figure
        plt.tight_layout()
        output_path = self.output_dir / f"{doc_name}_papermage_page_{page_idx+1}.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        
        if self.show_interactive:
            plt.show()
        else:
            plt.close(fig)
        
        return output_path
    
    def _visualize_comparisons(
        self, 
        doc_name: str, 
        pm_doc: Dict, 
        direct_pm_doc: Dict,
        pm_time: float,
        docling_time: float
    ) -> List[Path]:
        """
        Generate visualizations comparing the two document parsing results.
        
        Args:
            doc_name: Name of the document (used for output filenames)
            pm_doc: Document parsed with PaperMage-Docling
            direct_pm_doc: Document parsed directly with Docling
            pm_time: Time taken for PaperMage-Docling conversion
            docling_time: Time taken for direct Docling parsing
            
        Returns:
            List of paths to generated visualization files
        """
        output_paths = []
        
        # Compare entity counts
        stats_path = self._plot_statistics(
            doc_name, pm_doc, direct_pm_doc, pm_time, docling_time
        )
        if stats_path:
            output_paths.append(stats_path)
        
        # For each page, visualize layout comparison
        for page_idx in range(len(pm_doc.get("pages", []))):
            page_path = self._visualize_page_comparison(
                doc_name, page_idx, pm_doc, direct_pm_doc
            )
            if page_path:
                output_paths.append(page_path)
        
        return output_paths
    
    def _plot_statistics(
        self, 
        doc_name: str, 
        pm_doc: Dict, 
        direct_pm_doc: Dict,
        pm_time: float,
        docling_time: float
    ) -> Optional[Path]:
        """
        Generate statistical comparison of entity counts and performance.
        
        Args:
            doc_name: Name of the document
            pm_doc: Document parsed with PaperMage-Docling
            direct_pm_doc: Document parsed directly with Docling
            pm_time: Time taken for PaperMage-Docling conversion
            docling_time: Time taken for direct Docling parsing
            
        Returns:
            Path to the generated statistics visualization
        """
        # Count entities in both documents
        pm_counts = self._count_entities(pm_doc)
        direct_counts = self._count_entities(direct_pm_doc)
        
        # Set up the plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
        fig.suptitle(f"Document Parsing Comparison: {doc_name}", fontsize=16)
        
        # 1. Entity Count Comparison
        entity_types = sorted(set(list(pm_counts.keys()) + list(direct_counts.keys())))
        x = np.arange(len(entity_types))
        width = 0.35
        
        pm_values = [pm_counts.get(entity, 0) for entity in entity_types]
        direct_values = [direct_counts.get(entity, 0) for entity in entity_types]
        
        rects1 = ax1.bar(x - width/2, pm_values, width, label='PaperMage-Docling')
        rects2 = ax1.bar(x + width/2, direct_values, width, label='Direct Docling')
        
        ax1.set_title('Entity Count Comparison')
        ax1.set_ylabel('Count')
        ax1.set_xticks(x)
        ax1.set_xticklabels(entity_types, rotation=45, ha='right')
        ax1.legend()
        
        # Add count labels on bars
        def add_labels(rects):
            for rect in rects:
                height = rect.get_height()
                if height > 0:
                    ax1.annotate(f'{height}',
                                xy=(rect.get_x() + rect.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom')
        
        add_labels(rects1)
        add_labels(rects2)
        
        # 2. Performance Comparison
        labels = ['Processing Time']
        pm_perf = [pm_time]
        direct_perf = [docling_time]
        
        x = np.arange(len(labels))
        
        rects3 = ax2.bar(x - width/2, pm_perf, width, label='PaperMage-Docling')
        rects4 = ax2.bar(x + width/2, direct_perf, width, label='Direct Docling')
        
        ax2.set_title('Performance Comparison')
        ax2.set_ylabel('Time (seconds)')
        ax2.set_xticks(x)
        ax2.set_xticklabels(labels)
        ax2.legend()
        
        # Add time labels on bars
        for rect, time_val in zip([rects3[0], rects4[0]], [pm_time, docling_time]):
            height = rect.get_height()
            ax2.annotate(f'{time_val:.2f}s',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')
        
        plt.tight_layout()
        
        # Save the figure
        output_path = self.output_dir / f"{doc_name}_statistics.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        
        if self.show_interactive:
            plt.show()
        else:
            plt.close(fig)
        
        return output_path
    
    def _visualize_page_comparison(
        self, 
        doc_name: str, 
        page_idx: int, 
        pm_doc: Dict, 
        direct_pm_doc: Dict
    ) -> Optional[Path]:
        """
        Generate visualization comparing layout detection for a specific page.
        
        Args:
            doc_name: Name of the document
            page_idx: Index of the page to visualize
            pm_doc: Document parsed with PaperMage-Docling
            direct_pm_doc: Document parsed directly with Docling
            
        Returns:
            Path to the generated page comparison visualization
        """
        # Check if page exists in both documents
        pm_pages = pm_doc.get("pages", [])
        direct_pages = direct_pm_doc.get("pages", [])
        
        if page_idx >= len(pm_pages) or page_idx >= len(direct_pages):
            logger.warning(f"Page {page_idx} not found in both documents")
            return None
        
        pm_page = pm_pages[page_idx]
        direct_page = direct_pages[page_idx]
        
        # Set up the plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 10))
        fig.suptitle(f"Page {page_idx+1} Comparison: {doc_name}", fontsize=16)
        
        # Plot PaperMage-Docling results
        ax1.set_title("PaperMage-Docling")
        self._plot_page_entities(ax1, pm_doc, page_idx)
        
        # Plot Direct Docling results
        ax2.set_title("Direct Docling")
        self._plot_page_entities(ax2, direct_pm_doc, page_idx)
        
        plt.tight_layout()
        
        # Save the figure
        output_path = self.output_dir / f"{doc_name}_page_{page_idx+1}.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        
        if self.show_interactive:
            plt.show()
        else:
            plt.close(fig)
        
        return output_path
    
    def _plot_page_entities(self, ax, doc: Dict, page_idx: int):
        """
        Plot entity bounding boxes on a page.
        
        Args:
            ax: Matplotlib axis to plot on
            doc: Document dictionary
            page_idx: Index of the page to visualize
        """
        # Get page dimensions
        pages = doc.get("pages", [])
        if not pages or page_idx >= len(pages):
            return
        
        page = pages[page_idx]
        width = page.get("width", 612)  # Default letter width
        height = page.get("height", 792)  # Default letter height
        
        # Check for invalid dimensions and set reasonable defaults if needed
        if width <= 1 or height <= 1:
            logger.warning(f"Invalid page dimensions detected: {width}x{height}. Using defaults.")
            width = 612  # Standard letter width in points
            height = 792  # Standard letter height in points
        
        # Set axis limits with a small margin
        margin = max(width, height) * 0.05
        ax.set_xlim(-margin, width + margin)
        ax.set_ylim(-margin, height + margin)
        ax.invert_yaxis()  # Origin at top-left
        
        # Add basic grid for reference
        ax.grid(True, linestyle='--', alpha=0.3)
        
        # Plot page boundaries
        ax.add_patch(plt.Rectangle((0, 0), width, height, linewidth=2,
                                edgecolor='black', facecolor='none'))
        
        # Define colors for different entity types
        colors = {
            "words": "blue",
            "lines": "green",
            "paragraphs": "red",
            "tables": "purple",
            "table_cells": "magenta",
            "figures": "orange",
            "formulas": "cyan",
        }
        
        # Track which entity types actually have content for the legend
        shown_entities = set()
        
        # 1. Check for Page.words (Spans with box)
        if hasattr(page, "words") and page.words:
            shown_entities.add("words")
            for word in page.words:
                if hasattr(word, "box") and word.box:
                    # Extract coordinates
                    box = word.box
                    if hasattr(box, "x0") and hasattr(box, "y0") and hasattr(box, "x1") and hasattr(box, "y1"):
                        x = box.x0
                        y = box.y0
                        w = box.x1 - box.x0
                        h = box.y1 - box.y0
                        rect = plt.Rectangle((x, y), w, h, linewidth=1, 
                                         edgecolor=colors["words"], facecolor='none', alpha=0.5)
                        ax.add_patch(rect)
        # 2. Check for words in page dictionary format
        elif isinstance(page, dict) and "words" in page and isinstance(page["words"], list):
            shown_entities.add("words")
            for word in page["words"]:
                if isinstance(word, dict) and "box" in word and isinstance(word["box"], dict):
                    box = word["box"]
                    if all(k in box for k in ["x0", "y0", "x1", "y1"]):
                        x = box["x0"]
                        y = box["y0"]
                        w = box["x1"] - box["x0"]
                        h = box["y1"] - box["y0"]
                        rect = plt.Rectangle((x, y), w, h, linewidth=1, 
                                         edgecolor=colors["words"], facecolor='none', alpha=0.5)
                        ax.add_patch(rect)
                        
                        # Optionally show text for words
                        if "text" in word and ax.get_window_extent().width > 500:  # Only for large plots
                            ax.text(x, y-2, word["text"], fontsize=6, color=colors["words"], 
                                   rotation=0, ha='left', va='bottom')
        
        # 3. Plot entities from the standard structure
        entities = doc.get("entities", {})
        
        for entity_type, color in colors.items():
            if entity_type not in entities:
                continue
            
            entity_list = entities[entity_type]
            if not entity_list:
                continue
                
            for entity in entity_list:
                # Check if entity is on this page
                entity_page = entity.get("page")
                # Some entity structures might use page_idx directly, others might use page number (1-based)
                if entity_page is not None and entity_page != page_idx and entity_page != page_idx + 1:
                    continue
                
                # Extract bounding box - handle different possible formats
                bbox = None
                
                # Case 1: Direct bbox array [x, y, w, h]
                if "bbox" in entity and isinstance(entity["bbox"], (list, tuple)) and len(entity["bbox"]) == 4:
                    bbox = entity["bbox"]
                    x, y, w, h = bbox
                
                # Case 2: Nested bbox object with x0, y0, x1, y1
                elif "bbox" in entity and isinstance(entity["bbox"], dict) and all(k in entity["bbox"] for k in ["x0", "y0", "x1", "y1"]):
                    box = entity["bbox"]
                    x, y = box["x0"], box["y0"]
                    w, h = box["x1"] - box["x0"], box["y1"] - box["y0"]
                    bbox = [x, y, w, h]
                
                # Case 3: Direct properties on entity
                elif all(k in entity for k in ["x0", "y0", "x1", "y1"]):
                    x, y = entity["x0"], entity["y0"]
                    w, h = entity["x1"] - entity["x0"], entity["y1"] - entity["y0"]
                    bbox = [x, y, w, h]
                
                # Case 4: Box property with coordinates
                elif "box" in entity and isinstance(entity["box"], dict) and all(k in entity["box"] for k in ["x0", "y0", "x1", "y1"]):
                    box = entity["box"]
                    x, y = box["x0"], box["y0"]
                    w, h = box["x1"] - box["x0"], box["y1"] - box["y0"]
                    bbox = [x, y, w, h]
                
                if bbox:
                    x, y, w, h = bbox
                    # Skip entities with invalid coordinates or zero dimensions
                    if w <= 0 or h <= 0 or x < 0 or y < 0 or x > width or y > height:
                        continue
                        
                    rect = plt.Rectangle((x, y), w, h, linewidth=1, 
                                        edgecolor=color, facecolor='none', alpha=0.7)
                    ax.add_patch(rect)
                    shown_entities.add(entity_type)
                    
                    # Add label for tables and figures
                    if entity_type in ["tables", "figures"]:
                        if "id" in entity:
                            ax.text(x, y-5, entity["id"], fontsize=8, color=color)
                    
                    # Show text for words if available and plot is large enough
                    if entity_type == "words" and "text" in entity and ax.get_window_extent().width > 500:
                        ax.text(x, y-2, entity["text"], fontsize=6, color=color, 
                               rotation=0, ha='left', va='bottom')
        
        # Add legend only for entity types actually shown
        if shown_entities:
            legend_elements = [
                plt.Rectangle((0, 0), 1, 1, edgecolor=colors.get(entity_type, "gray"), 
                              facecolor='none', label=entity_type)
                for entity_type in shown_entities
            ]
            ax.legend(handles=legend_elements, loc='upper right')
        else:
            # If no entities were found, add a note
            ax.text(width/2, height/2, "No entities found on this page", 
                    ha='center', va='center', fontsize=12, color='red',
                    bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.5'))
        
        # Draw basic X and Y axes with ticks for reference
        ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
        ax.axvline(x=0, color='k', linestyle='-', alpha=0.3)
        
        # Add page information
        page_info = f"Page {page_idx+1} ({width:.1f}x{height:.1f})"
        ax.set_title(page_info)
        
        # Set aspect ratio
        ax.set_aspect('equal')
    
    def _count_entities(self, doc: Dict) -> Dict[str, int]:
        """
        Count entities by type in a document.
        
        Args:
            doc: Document dictionary
            
        Returns:
            Dictionary mapping entity types to counts
        """
        counts = {}
        entities = doc.get("entities", {})
        
        for entity_type, entity_list in entities.items():
            counts[entity_type] = len(entity_list)
        
        return counts


def main():
    """
    Main function to run as a CLI tool.
    
    Usage:
        python -m papermage_docling.visualizers.comparison_visualizer path/to/document.pdf
    """
    import argparse
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    # Check prerequisites
    if not VISUALIZATION_AVAILABLE:
        logger.error("Visualization libraries not available. Please install required packages:")
        logger.error("pip install matplotlib numpy pillow")
        return 1
    
    if not DOCLING_AVAILABLE:
        logger.warning("Docling is not available. Will proceed with PaperMage-only visualizations.")
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Compare document parsing between PaperMage-Docling and direct Docling"
    )
    
    parser.add_argument(
        "pdf_file",
        type=str,
        help="Path to the PDF file to compare"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./comparisons",
        help="Directory to save visualizations"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Open visualizations in interactive mode"
    )
    
    parser.add_argument(
        "--enable-ocr",
        action="store_true",
        help="Enable OCR for scanned documents"
    )
    
    parser.add_argument(
        "--no-tables",
        action="store_true",
        help="Disable table detection"
    )
    
    parser.add_argument(
        "--no-figures",
        action="store_true",
        help="Disable figure detection"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        logger.error(f"PDF file not found: {pdf_path}")
        return 1
    
    # Setup conversion options
    options = {
        "detect_tables": not args.no_tables,
        "detect_figures": not args.no_figures,
        "enable_ocr": args.enable_ocr,
    }
    
    # Create output directory
    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        os.makedirs(output_dir)
    
    # Initialize visualizer
    visualizer = ComparisonVisualizer(
        output_dir=output_dir,
        show_interactive=args.interactive
    )
    
    # Run comparison
    try:
        output_paths = visualizer.compare_documents(pdf_path, options)
        logger.info(f"Generated {len(output_paths)} visualizations:")
        for path in output_paths:
            logger.info(f"- {path}")
        return 0
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 