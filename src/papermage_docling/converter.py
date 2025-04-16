"""
New unified document conversion module using Docling directly.

This module provides a direct conversion from various document formats to the PaperMage JSON format
using Docling's DocumentConverter. This replaces the previous pipeline-based approach that used
multiple separate components (parsers, predictors, converters).
"""

import os
import logging
from typing import Any, Dict, List, Optional, Union, BinaryIO
from pathlib import Path

from docling.document_converter import DocumentConverter

# Import the Pydantic models for output format
from papermage_docling.converters.document import (
    Document, Page, Entity, Box, Span, TableEntity, FigureEntity
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
        options: Configuration options for conversion
    
    Returns:
        A dictionary representing the document in PaperMage JSON format
    
    Raises:
        ValueError: If the source cannot be read or the conversion fails
    """
    # Default options
    if options is None:
        options = {}
    
    try:
        # Setup Docling configuration
        converter_args = {
            "tables": options.get("detect_tables", True),
            "figures": options.get("detect_figures", True),
            "metadata": True,
            "ocr": options.get("enable_ocr", False),
            "parser": "doclingparse_v4",  # Explicitly use DoclingParse v4
            "rtl_enabled": options.get("detect_rtl", True),  # Enable RTL detection and processing
        }
        
        # Add OCR language if provided
        if "ocr_language" in options:
            converter_args["ocr_language"] = options["ocr_language"]

        # Create Docling DocumentConverter
        logger.info(f"Creating Docling DocumentConverter with DoclingParse v4")
        converter = DocumentConverter(**converter_args)
        
        # Convert the document
        logger.info(f"Converting document with Docling v4 (tables={converter_args['tables']}, figures={converter_args['figures']}, rtl={converter_args['rtl_enabled']})")
        
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
    
    # Process pages
    for page_idx, docling_page in enumerate(doc.pages):
        # Create Page
        page = Page(
            number=page_idx + 1,  # 1-indexed
            width=getattr(docling_page, "width", 0),
            height=getattr(docling_page, "height", 0),
            rotation=getattr(docling_page, "rotation", 0),
            words=[],
            entities=[]
        )
        
        # Process text and words
        if hasattr(docling_page, "text"):
            # Store page text for full_text
            all_text.append(docling_page.text)
            
            # Process words if available
            if hasattr(docling_page, "words"):
                for word_idx, word in enumerate(docling_page.words):
                    # Create word span
                    span = Span(
                        text=getattr(word, "text", ""),
                        box=Box(
                            x0=getattr(word, "x0", 0),
                            y0=getattr(word, "y0", 0),
                            x1=getattr(word, "x1", 0),
                            y1=getattr(word, "y1", 0)
                        )
                    )
                    page.words.append(span)
        
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
        "figures": figures
    }
    
    # Convert to dictionary
    return document.model_dump() 