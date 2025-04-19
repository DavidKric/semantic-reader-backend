"""
New unified document conversion module using Docling directly.

This module provides a direct conversion from various document formats to the PaperMage JSON format
using Docling's DocumentConverter. This replaces the previous pipeline-based approach that used
multiple separate components (parsers, predictors, converters).

Supported options:
- detect_tables: Enable table detection (default: True)
- detect_figures: Enable figure detection (default: True)
- enable_ocr: Enable OCR for scanned documents (default: False)
- ocr_language: OCR language code (e.g., 'eng', 'ara')
- detect_rtl: Enable RTL detection and processing (default: True)
- do_code_enrichment: Enable code block enrichment (default: False)
- do_formula_enrichment: Enable formula enrichment (default: False)
- do_picture_classification: Enable picture classification (default: False)
- do_table_structure: Enable table structure analysis (default: False)
- parser: Parser to use (default: 'doclingparse_v4')
- metadata: Include metadata (default: True)

Any additional options supported by Docling's DocumentConverter can be passed through.
"""

import logging
import os
from pathlib import Path
from typing import Any, BinaryIO, Dict, Optional, Union

try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    logging.warning("Docling not found. Document conversion will be unavailable.")

# Import the Pydantic models for output format
from papermage_docling.converters.document import (
    Box,
    Document,
    FigureEntity,
    Page,
    Span,
    TableEntity,
)

# Setup logging
logger = logging.getLogger(__name__)

# Define RTL languages
RTL_LANGUAGES = {'ar', 'he', 'fa', 'ur', 'dv', 'ha', 'khw', 'ks', 'ku', 'ps', 'sd', 'ug', 'yi'}

def convert_document(
    source: Union[str, Path, BinaryIO, bytes],
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Convert a document to PaperMage JSON format using Docling with DoclingParse v4.
    
    Args:
        source: Path to file, file-like object, or bytes of the document
        options: Configuration options for conversion (see module docstring)
    
    Returns:
        A dictionary representing the document in PaperMage JSON format
    
    Raises:
        ValueError: If the source cannot be read or the conversion fails
    """
    # Default options
    if options is None:
        options = {}
    
    try:
        # Build converter_args with all supported options
        # Check what version of Docling we're using - different versions have different expected args
        converter_args = {}
        
        # Handle parameters for Docling - check if available parameters
        # Note: Different versions of Docling may have different parameters
        if DOCLING_AVAILABLE:
            # Map our parameter names to Docling parameter names
            param_mapping = {
                "detect_tables": "detect_tables",
                "detect_figures": "detect_figures",
                "metadata": "extract_metadata",
                "enable_ocr": "ocr",
                "detect_rtl": "rtl_enabled",
                "parser": "parser"
            }
            
            # Check the signature of DocumentConverter to see which params it accepts
            import inspect
            dc_params = inspect.signature(DocumentConverter.__init__).parameters
            
            # Add only parameters that are accepted by the current Docling version
            for our_param, docling_param in param_mapping.items():
                if docling_param in dc_params:
                    converter_args[docling_param] = options.get(our_param, True)
                elif our_param in options:
                    logger.warning(f"Parameter '{our_param}' is not supported by this version of Docling")
            
            # Add other common parameters if they're available
            # OCR language
            if "ocr_language" in options and "ocr_language" in dc_params:
                converter_args["ocr_language"] = options["ocr_language"]
            
            # Advanced pipeline options if supported
            advanced_options = {
                "do_code_enrichment": "do_code_enrichment",
                "do_formula_enrichment": "do_formula_enrichment", 
                "do_picture_classification": "do_picture_classification",
                "do_table_structure": "do_table_structure"
            }
            
            for our_param, docling_param in advanced_options.items():
                if docling_param in dc_params and our_param in options:
                    converter_args[docling_param] = options[our_param]
        else:
            # Docling not available - can't convert
            raise ImportError("Docling is not available. Please install it to use this converter.")

        # Create Docling DocumentConverter
        logger.info(f"Creating Docling DocumentConverter with args: {converter_args}")
        converter = DocumentConverter(**converter_args)
        
        # Convert the document
        logger.info(f"Converting document with Docling v4")
        
        # Handle different source types
        if isinstance(source, (str, Path)):
            result = converter.convert(str(source))
        elif isinstance(source, bytes):
            # For bytes, we need to write to a temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(source)
                temp_file_path = temp_file.name
            
            try:
                result = converter.convert(temp_file_path)
            finally:
                # Clean up the temporary file
                os.unlink(temp_file_path)
        else:
            # For file-like objects
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(source.read())
                temp_file_path = temp_file.name
            
            try:
                result = converter.convert(temp_file_path)
            finally:
                # Clean up the temporary file
                os.unlink(temp_file_path)
        
        # Map DoclingDocument to PaperMage format
        return docling_to_papermage(result.document)
    
    except Exception as e:
        logger.error(f"Error converting document with Docling: {e}")
        raise ValueError(f"Failed to convert document: {e}") from e

def docling_to_papermage(doc: Any) -> Dict[str, Any]:
    """
    Map a Docling document to PaperMage JSON format.
    
    Args:
        doc: A DoclingDocument from Docling
    
    Returns:
        A dictionary in PaperMage JSON format
    """
    # Create Document model
    document = Document(
        id=getattr(doc, "id", None) or "doc-1",
        metadata={},
        pages=[],
        full_text=""
    )
    
    # Process metadata
    if hasattr(doc, "metadata") and doc.metadata:
        document.metadata = {
            "language": getattr(doc.metadata, "language", "en"),
            "title": getattr(doc.metadata, "title", ""),
            "authors": getattr(doc.metadata, "authors", []),
            "creation_date": getattr(doc.metadata, "creation_date", ""),
            "modification_date": getattr(doc.metadata, "modification_date", ""),
        }
        
        # Add is_rtl flag (maintaining legacy format)
        language_code = document.metadata.get("language", "en")
        document.metadata["is_rtl_language"] = language_code in RTL_LANGUAGES
    
    # Initialize variables for full text and entities
    all_text = []
    tables = []
    figures = []
    words = []
    
    # Process pages
    for page_idx, docling_page in enumerate(doc.pages):
        # Get page dimensions from PDF page if available
        page_width = 0
        page_height = 0
        
        # Try different ways to get the page dimensions
        if hasattr(docling_page, "width") and hasattr(docling_page, "height"):
            page_width = getattr(docling_page, "width", 0)
            page_height = getattr(docling_page, "height", 0)
        elif hasattr(docling_page, "page_dimensions"):
            dim = getattr(docling_page, "page_dimensions", None)
            if dim and len(dim) >= 2:
                page_width, page_height = dim[0], dim[1]
        # As a fallback, try to get dimensions from the original PDF page
        elif hasattr(docling_page, "_pdf_page") and hasattr(docling_page._pdf_page, "get_dimensions"):
            try:
                dim = docling_page._pdf_page.get_dimensions()
                if dim and len(dim) >= 2:
                    page_width, page_height = dim[0], dim[1]
            except:
                pass  # Ignore errors if we can't access PDF dimensions
                
        # Use default letter sizes if dimensions are still zero or invalid
        if page_width <= 1 or page_height <= 1:
            logger.warning(f"Invalid or missing page dimensions for page {page_idx+1}, using defaults.")
            page_width = 612  # Standard letter width in points (8.5 inches)
            page_height = 792  # Standard letter height in points (11 inches)
            
        # Create Page
        page = Page(
            number=page_idx + 1,  # 1-indexed
            width=page_width,
            height=page_height,
            rotation=getattr(docling_page, "rotation", 0),
            words=[],
            entities=[]
        )
        
        # Process text and words
        if hasattr(docling_page, "text"):
            # Store page text for full_text
            all_text.append(docling_page.text)
            
            # Process words if available
            if hasattr(docling_page, "words") and docling_page.words:
                for word_idx, word in enumerate(docling_page.words):
                    # Get word text and position
                    word_text = getattr(word, "text", "")
                    
                    # Skip empty words
                    if not word_text:
                        continue
                    
                    # Get word bounding box
                    x0 = getattr(word, "x0", 0)
                    y0 = getattr(word, "y0", 0)
                    x1 = getattr(word, "x1", 0)
                    y1 = getattr(word, "y1", 0)
                    
                    # Skip words with invalid or zero dimensions
                    if x0 >= x1 or y0 >= y1:
                        logger.debug(f"Skipping word with invalid dimensions: {word_text} ({x0},{y0},{x1},{y1})")
                        continue
                    
                    # Verify word is on the page
                    if x1 > page_width:
                        x1 = page_width
                    if y1 > page_height:
                        y1 = page_height
                    
                    # Create word span
                    span = Span(
                        text=word_text,
                        box=Box(
                            x0=x0,
                            y0=y0,
                            x1=x1,
                            y1=y1
                        )
                    )
                    page.words.append(span)
                    
                    # Also add to entities words list
                    word_entity = {
                        "page": page_idx,
                        "bbox": [x0, y0, x1-x0, y1-y0],
                        "text": word_text
                    }
                    words.append(word_entity)
        
        # Process tables
        if hasattr(docling_page, "tables") and docling_page.tables:
            for table_idx, table in enumerate(docling_page.tables):
                # Create table entity
                table_entity = TableEntity(
                    id=f"table-{page_idx+1}-{table_idx+1}",
                    box=Box(
                        x0=getattr(table, "x0", 0),
                        y0=getattr(table, "y0", 0),
                        x1=getattr(table, "x1", 0),
                        y1=getattr(table, "y1", 0)
                    ),
                    rows=[],
                    columns=[],
                    caption=getattr(table, "caption", "") or ""
                )
                
                # Process rows and cells
                if hasattr(table, "rows") and table.rows:
                    for row_idx, row in enumerate(table.rows):
                        table_row = []
                        if hasattr(row, "cells") and row.cells:
                            for cell_idx, cell in enumerate(row.cells):
                                cell_text = getattr(cell, "text", "")
                                table_row.append(cell_text)
                        table_entity.rows.append(table_row)
                
                # Add to page entities and global tables list
                page.entities.append(table_entity)
                tables.append(table_entity)
        
        # Process figures
        if hasattr(docling_page, "figures") and docling_page.figures:
            for figure_idx, figure in enumerate(docling_page.figures):
                # Create figure entity
                figure_entity = FigureEntity(
                    id=f"figure-{page_idx+1}-{figure_idx+1}",
                    box=Box(
                        x0=getattr(figure, "x0", 0),
                        y0=getattr(figure, "y0", 0),
                        x1=getattr(figure, "x1", 0),
                        y1=getattr(figure, "y1", 0)
                    ),
                    caption=getattr(figure, "caption", "") or ""
                )
                
                # Add to page entities and global figures list
                page.entities.append(figure_entity)
                figures.append(figure_entity)
        
        # Add page to document
        document.pages.append(page)
    
    # Set full text
    document.full_text = "\n".join(all_text)
    
    # Add entities section at the document level
    document.entities = {
        "tables": tables,
        "figures": figures,
        "words": words
    }
    
    # Convert to dictionary
    return document.model_dump()

class DoclingToPapermageConverter:
    """
    Converter class that wraps the conversion functions for object-oriented usage.
    This class provides backward compatibility with older code expecting a converter object.
    """
    
    def __init__(self, **options):
        """
        Initialize the converter with options.
        
        Args:
            **options: Options to pass to convert_document
        """
        self.options = options
    
    def convert(self, source: Union[str, Path, BinaryIO, bytes]) -> Dict[str, Any]:
        """
        Convert a document to PaperMage JSON format.
        
        Args:
            source: Path to file, file-like object, or bytes of the document
            
        Returns:
            A dictionary representing the document in PaperMage JSON format
        """
        return convert_document(source, self.options)
    
    @staticmethod
    def docling_to_papermage(doc: Any) -> Dict[str, Any]:
        """
        Map a Docling document to PaperMage JSON format.
        
        Args:
            doc: A DoclingDocument from Docling
            
        Returns:
            A dictionary in PaperMage JSON format
        """
        return docling_to_papermage(doc) 