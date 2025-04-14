"""
Table prediction and structure analysis using Docling's native table capabilities.

This module provides functionality for detecting tables in documents and
analyzing their structure (rows, columns, cells) using Docling's table models.
"""

import logging
import os
from typing import Dict, List, Optional, Union, Any, Tuple, BinaryIO
from pathlib import Path
import json
import pandas as pd
import numpy as np

# Import Docling document structures
try:
    from docling_core.types import DoclingDocument
    from docling_parse.pdf_parser import PdfDocument
    from docling_core.types.doc import Page, TextCellUnit
    # Import table models if available
    try:
        from docling.models.table_structure_model import TableStructureModel
        HAS_TABLE_MODELS = True
    except ImportError:
        logging.warning("Docling table models not found. Using basic table detection.")
        HAS_TABLE_MODELS = False
except ImportError:
    logging.warning("Docling dependencies not found. Table prediction functionality will be limited.")
    # Define stub classes for type hints
    class DoclingDocument:
        pass
    
    class PdfDocument:
        pass
    
    class Page:
        pass
    
    class TextCellUnit:
        CHAR = "char"
        WORD = "word"
        LINE = "line"
        PARAGRAPH = "paragraph"
    
    HAS_TABLE_MODELS = False

# Import rasterizer for table detection
from papermage_docling.rasterizers import PDFRasterizer, get_pdf_rasterizer

logger = logging.getLogger(__name__)


class TableItem:
    """
    Represents a table with its structure and content.
    
    This class encapsulates a table's metadata, structure (rows, columns, cells),
    and content, providing methods for accessing and manipulating the table.
    """
    
    def __init__(
        self,
        page_idx: int,
        table_idx: int,
        bbox: Tuple[float, float, float, float],
        rows: int = 0,
        cols: int = 0,
        cells: Optional[List[Dict[str, Any]]] = None,
        confidence: float = 0.0
    ):
        """
        Initialize a table item with its metadata and structure.
        
        Args:
            page_idx: Page index where the table appears
            table_idx: Index of the table on the page
            bbox: Bounding box of the table (x0, y0, x1, y1) in PDF coordinates
            rows: Number of rows in the table
            cols: Number of columns in the table
            cells: List of cell dictionaries with cell data
            confidence: Detection confidence score (0.0 to 1.0)
        """
        self.page_idx = page_idx
        self.table_idx = table_idx
        self.bbox = bbox
        self.rows = rows
        self.cols = cols
        self.cells = cells or []
        self.confidence = confidence
        self.caption = None
        self.metadata = {}
    
    def set_caption(self, caption_text: str, caption_bbox: Optional[Tuple[float, float, float, float]] = None) -> None:
        """
        Set the caption for this table.
        
        Args:
            caption_text: Text of the caption
            caption_bbox: Optional bounding box of the caption
        """
        self.caption = {
            "text": caption_text,
            "bbox": caption_bbox
        }
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the table to a pandas DataFrame.
        
        Returns:
            DataFrame representation of the table
        """
        # Extract data from cells
        data = []
        max_row = max(cell.get("row_idx", 0) for cell in self.cells) if self.cells else 0
        max_col = max(cell.get("col_idx", 0) for cell in self.cells) if self.cells else 0
        
        # Initialize empty DataFrame with correct dimensions
        df = pd.DataFrame(np.empty((max_row + 1, max_col + 1), dtype=object))
        
        # Fill in cell values
        for cell in self.cells:
            row_idx = cell.get("row_idx", 0)
            col_idx = cell.get("col_idx", 0)
            text = cell.get("text", "")
            
            # Handle merged cells (rowspan, colspan)
            rowspan = cell.get("rowspan", 1)
            colspan = cell.get("colspan", 1)
            
            # Fill the main cell
            df.iloc[row_idx, col_idx] = text
            
            # Mark merged cells with None
            for r in range(row_idx, row_idx + rowspan):
                for c in range(col_idx, col_idx + colspan):
                    if r != row_idx or c != col_idx:
                        df.iloc[r, c] = None
        
        # Clean up any remaining NaN values
        df = df.fillna("")
        
        # Try to use the first row as header if it seems like a header
        if len(df) > 1:
            try:
                # Check if first row looks like a header (e.g., different format or all non-empty)
                first_row = df.iloc[0]
                if all(str(val).strip() for val in first_row):
                    headers = first_row.tolist()
                    df = df.iloc[1:].copy()
                    df.columns = headers
            except Exception as e:
                logger.warning(f"Failed to set DataFrame headers: {e}")
        
        return df
    
    def to_html(self) -> str:
        """
        Convert the table to HTML format.
        
        Returns:
            HTML representation of the table
        """
        df = self.to_dataframe()
        html = df.to_html(index=False)
        
        # Add caption if available
        if self.caption:
            caption_text = self.caption["text"]
            html = html.replace("<table", f"<table id='table-{self.page_idx}-{self.table_idx}'")
            html = html.replace("<table", f"<table caption='{caption_text}'")
        
        return html
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the table to a dictionary representation.
        
        Returns:
            Dictionary representation of the table
        """
        return {
            "page_idx": self.page_idx,
            "table_idx": self.table_idx,
            "bbox": self.bbox,
            "rows": self.rows,
            "cols": self.cols,
            "cells": self.cells,
            "confidence": self.confidence,
            "caption": self.caption,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TableItem':
        """
        Create a TableItem from a dictionary representation.
        
        Args:
            data: Dictionary representation of the table
            
        Returns:
            TableItem instance
        """
        table = cls(
            page_idx=data.get("page_idx", 0),
            table_idx=data.get("table_idx", 0),
            bbox=data.get("bbox", (0, 0, 0, 0)),
            rows=data.get("rows", 0),
            cols=data.get("cols", 0),
            cells=data.get("cells", []),
            confidence=data.get("confidence", 0.0)
        )
        
        if "caption" in data:
            table.caption = data["caption"]
        
        if "metadata" in data:
            table.metadata = data["metadata"]
        
        return table


class TablePredictor:
    """
    Table prediction and structure analysis using Docling's native table capabilities.
    
    This class leverages Docling's table detection and structure analysis models
    to identify tables in documents and analyze their structure.
    """
    
    def __init__(
        self,
        table_confidence_threshold: float = 0.5,
        enable_structure_analysis: bool = True,
        enable_cell_extraction: bool = True,
        enable_caption_detection: bool = True,
        rasterizer: Optional[PDFRasterizer] = None,
        custom_models_path: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the table predictor with configuration options.
        
        Args:
            table_confidence_threshold: Minimum confidence for table detection
            enable_structure_analysis: Whether to analyze table structure (rows, columns)
            enable_cell_extraction: Whether to extract cell content
            enable_caption_detection: Whether to detect and link table captions
            rasterizer: Optional PDFRasterizer instance for page image generation
            custom_models_path: Path to custom table models (if any)
            **kwargs: Additional configuration options
        """
        self.table_confidence_threshold = table_confidence_threshold
        self.enable_structure_analysis = enable_structure_analysis
        self.enable_cell_extraction = enable_cell_extraction
        self.enable_caption_detection = enable_caption_detection
        self.custom_models_path = custom_models_path
        self.config = kwargs
        
        # Get or create rasterizer
        self.rasterizer = rasterizer or get_pdf_rasterizer()
        
        logger.info(
            f"Initializing TablePredictor (confidence threshold: {table_confidence_threshold}, "
            f"structure analysis: {enable_structure_analysis}, "
            f"cell extraction: {enable_cell_extraction})"
        )
        
        # Initialize table structure model if available
        self.table_model = None
        
        if HAS_TABLE_MODELS:
            try:
                self.table_model = TableStructureModel(
                    confidence_threshold=table_confidence_threshold,
                    model_path=custom_models_path,
                    **kwargs
                )
                logger.info("Successfully initialized Docling TableStructureModel")
            except Exception as e:
                logger.error(f"Failed to initialize Docling TableStructureModel: {e}")
        else:
            logger.warning(
                "Docling table models not available. "
                "Using basic table detection with limited capabilities."
            )
    
    def predict(
        self, 
        document: Union[PdfDocument, str, Path, BinaryIO],
        **kwargs
    ) -> List[TableItem]:
        """
        Detect tables in a document and analyze their structure.
        
        Args:
            document: PdfDocument, path to PDF file, or file-like object
            **kwargs: Additional processing options
            
        Returns:
            List of TableItem objects representing detected tables
        """
        logger.info("Starting table detection and analysis")
        
        tables = []
        
        # Use Docling's table model if available
        if self.table_model and HAS_TABLE_MODELS:
            try:
                # Process document using Docling's table model
                detected_tables = self.table_model.detect_tables(document)
                
                # Convert Docling table representations to TableItems
                for table_idx, table_data in enumerate(detected_tables):
                    table_item = self._convert_docling_table(table_data, table_idx)
                    if table_item:
                        tables.append(table_item)
                
                logger.info(f"Detected {len(tables)} tables using Docling's TableStructureModel")
                return tables
            except Exception as e:
                logger.warning(f"Error using Docling table model: {e}. Falling back to basic detection.")
        
        # Fallback to basic table detection
        try:
            # Open PDF document if needed
            pdf_doc = self._get_pdf_document(document)
            
            # Detect tables using basic heuristics
            tables = self._detect_tables_basic(pdf_doc)
            
            logger.info(f"Detected {len(tables)} tables using basic heuristics")
            return tables
        except Exception as e:
            logger.error(f"Error detecting tables: {e}")
            return []
    
    def predict_docling(self, doc: DoclingDocument, **kwargs) -> DoclingDocument:
        """
        Detect tables in a DoclingDocument and update it with the results.
        
        This method processes the document using Docling's native format end-to-end,
        without converting to intermediate formats.
        
        Args:
            doc: DoclingDocument to process
            **kwargs: Additional processing options
            
        Returns:
            Updated DoclingDocument with detected tables
        """
        logger.info("Starting table detection and analysis on DoclingDocument")
        
        # Import necessary classes
        from docling_core.types import TableItem as DoclingTableItem
        import uuid
        
        # Get existing table IDs to avoid duplicates
        existing_table_ids = {table.id for table in doc.tables}
        
        # Use visual-based table detection methods since TableItem contains
        # detection results; not limited to tables in DoclingDocument
        tables = []
        
        # Process each page's text content to find table regions
        text_by_page = {}
        for text_item in doc.texts:
            page = text_item.page
            if page not in text_by_page:
                text_by_page[page] = []
            text_by_page[page].append(text_item)
        
        # For each page, analyze text layout to detect potential table regions
        for page_num, text_items in text_by_page.items():
            # Sort text items by vertical position
            text_items.sort(key=lambda x: x.bbox[1])
            
            # Look for tabular patterns
            table_regions = self._identify_table_regions(text_items)
            
            for region_idx, region in enumerate(table_regions):
                # Get text lines in the region
                region_items = region["items"]
                region_bbox = region["bbox"]
                
                # Only process regions that look like tables
                if not self._is_likely_table(region_items):
                    continue
                
                # Extract table structure
                num_rows = len(region_items)
                num_cols = self._estimate_columns(region_items)
                
                # Generate unique ID
                table_id = str(uuid.uuid4())
                while table_id in existing_table_ids:
                    table_id = str(uuid.uuid4())
                
                # Extract cells
                cells = self._extract_cells_from_items(region_items, num_cols)
                
                # Create table item
                table_item = DoclingTableItem(
                    id=table_id,
                    page=page_num,
                    bbox=region_bbox,
                    rows=num_rows,
                    columns=num_cols,
                    cells=cells,
                    metadata={"confidence": 0.8, "source": "docling_predictor"}
                )
                
                # Add caption if found
                caption = self._find_caption_for_region(text_items, region_bbox)
                if caption:
                    table_item.caption = caption
                
                # Add to tables list
                doc.tables.append(table_item)
        
        # If using the Docling table model, use its results too
        if self.table_model and HAS_TABLE_MODELS:
            try:
                # Convert DoclingDocument to a format the table model can process
                # For example, we might need to create a temp PDF or use page images
                # This is a simplified placeholder - actual implementation would depend
                # on the table model's requirements
                detected_tables = self._detect_tables_with_model(doc)
                
                # Add detected tables to the document
                for table_data in detected_tables:
                    # Generate unique ID
                    table_id = str(uuid.uuid4())
                    while table_id in existing_table_ids:
                        table_id = str(uuid.uuid4())
                    
                    # Create table item
                    table_item = DoclingTableItem(
                        id=table_id,
                        page=table_data.get("page_num", 1),
                        bbox=table_data.get("bbox", [0, 0, 0, 0]),
                        rows=table_data.get("num_rows", 0),
                        columns=table_data.get("num_cols", 0),
                        cells=table_data.get("cells", []),
                        metadata={"confidence": table_data.get("confidence", 0.7), 
                                  "source": "docling_table_model"}
                    )
                    
                    # Add caption if available
                    if "caption" in table_data:
                        table_item.caption = table_data["caption"].get("text", "")
                    
                    # Add to tables list
                    doc.tables.append(table_item)
                    
                logger.info(f"Added {len(detected_tables)} tables from Docling TableStructureModel")
            except Exception as e:
                logger.warning(f"Error using Docling table model: {e}")
        
        logger.info(f"Total tables in updated DoclingDocument: {len(doc.tables)}")
        return doc
    
    def _identify_table_regions(self, text_items):
        """Identify regions that might contain tables based on text layout."""
        regions = []
        
        # A basic heuristic: look for sequences of lines with similar formatting
        # and consistent spacing/alignment that might indicate a table
        current_region = {"items": [], "bbox": None}
        items_by_line = {}
        
        # Group items by their vertical position (approximate lines)
        for item in text_items:
            y_mid = (item.bbox[1] + item.bbox[3]) / 2
            line_idx = int(y_mid * 100)  # Quantize to handle minor variations
            
            if line_idx not in items_by_line:
                items_by_line[line_idx] = []
            
            items_by_line[line_idx].append(item)
        
        # Sort lines by vertical position
        sorted_line_idxs = sorted(items_by_line.keys())
        
        in_table = False
        for i, line_idx in enumerate(sorted_line_idxs):
            line_items = items_by_line[line_idx]
            
            # Sort items horizontally
            line_items.sort(key=lambda x: x.bbox[0])
            
            # Check if line has table-like properties
            # (e.g., multiple items with consistent spacing)
            if len(line_items) >= 3:
                # Calculate spacing between items
                spaces = []
                for j in range(1, len(line_items)):
                    space = line_items[j].bbox[0] - line_items[j-1].bbox[2]
                    spaces.append(space)
                
                # Check if spacing is consistent (approximate)
                mean_space = sum(spaces) / len(spaces)
                std_space = sum((s - mean_space) ** 2 for s in spaces) ** 0.5
                
                is_table_row = std_space < 0.2 * mean_space  # Adjust threshold as needed
            else:
                is_table_row = False
            
            # Handle table boundary detection
            if is_table_row and not in_table:
                # Start of a new table
                in_table = True
                current_region = {"items": [line_items], "bbox": None}
            elif is_table_row and in_table:
                # Continue current table
                current_region["items"].append(line_items)
            elif not is_table_row and in_table:
                # End of current table
                if len(current_region["items"]) >= 2:  # Minimum two rows for a table
                    # Calculate bounding box
                    x0 = min(item.bbox[0] for row in current_region["items"] for item in row)
                    y0 = min(item.bbox[1] for row in current_region["items"] for item in row)
                    x1 = max(item.bbox[2] for row in current_region["items"] for item in row)
                    y1 = max(item.bbox[3] for row in current_region["items"] for item in row)
                    
                    current_region["bbox"] = [x0, y0, x1, y1]
                    regions.append(current_region)
                
                in_table = False
        
        # Handle case where document ends with a table
        if in_table and len(current_region["items"]) >= 2:
            x0 = min(item.bbox[0] for row in current_region["items"] for item in row)
            y0 = min(item.bbox[1] for row in current_region["items"] for item in row)
            x1 = max(item.bbox[2] for row in current_region["items"] for item in row)
            y1 = max(item.bbox[3] for row in current_region["items"] for item in row)
            
            current_region["bbox"] = [x0, y0, x1, y1]
            regions.append(current_region)
        
        return regions
    
    def _is_likely_table(self, rows):
        """Determine if a region is likely to be a table based on row structure."""
        if len(rows) < 2:
            return False
        
        # Check if rows have similar number of items
        item_counts = [len(row) for row in rows]
        mean_count = sum(item_counts) / len(item_counts)
        
        # Allow some variation, but most rows should have a similar structure
        consistent_rows = sum(1 for count in item_counts if abs(count - mean_count) <= 1)
        return consistent_rows >= 0.7 * len(rows)  # At least 70% of rows are consistent
    
    def _estimate_columns(self, rows):
        """Estimate the number of columns in a table region."""
        # Use the most common number of items per row as the column count
        item_counts = [len(row) for row in rows]
        count_freq = {}
        for count in item_counts:
            count_freq[count] = count_freq.get(count, 0) + 1
        
        # Get the most common count
        most_common = max(count_freq.items(), key=lambda x: x[1])[0]
        return most_common
    
    def _extract_cells_from_items(self, rows, num_cols):
        """Extract cell data from text items."""
        cells = []
        
        for row_idx, row in enumerate(rows):
            # Sort items horizontally
            row.sort(key=lambda x: x.bbox[0])
            
            # If row has fewer items than expected columns, adjust
            actual_cols = len(row)
            col_ratio = num_cols / max(1, actual_cols)
            
            for col_idx, item in enumerate(row):
                # Calculate column span if items are fewer than expected
                colspan = round(col_ratio) if col_ratio > 1 else 1
                
                cell = {
                    "row_idx": row_idx,
                    "col_idx": col_idx,
                    "text": item.text,
                    "bbox": item.bbox,
                    "rowspan": 1,
                    "colspan": colspan
                }
                cells.append(cell)
        
        return cells
    
    def _find_caption_for_region(self, text_items, region_bbox):
        """Find a potential caption for a table region."""
        # Look for captions that typically appear above or below tables
        # and often start with "Table" or similar indicator
        
        x0, y0, x1, y1 = region_bbox
        width = x1 - x0
        
        candidates = []
        
        # Check items above and below the region
        for item in text_items:
            item_y_mid = (item.bbox[1] + item.bbox[3]) / 2
            item_x_mid = (item.bbox[0] + item.bbox[2]) / 2
            
            # Check if horizontally aligned with the table
            is_horizontally_aligned = (
                item_x_mid >= x0 - 0.1 * width and 
                item_x_mid <= x1 + 0.1 * width
            )
            
            # Check if vertically close to the table
            is_above = (
                item.bbox[3] < y0 and
                y0 - item.bbox[3] < 0.05  # Within 5% of page height
            )
            
            is_below = (
                item.bbox[1] > y1 and
                item.bbox[1] - y1 < 0.05  # Within 5% of page height
            )
            
            if is_horizontally_aligned and (is_above or is_below):
                text = item.text.lower()
                # Higher score for items that start with "table"
                score = 3 if text.startswith("table") else 1
                # Higher score for closer items
                distance = min(abs(y0 - item.bbox[3]), abs(item.bbox[1] - y1))
                score -= distance * 10  # Penalize by distance
                
                candidates.append((item, score))
        
        # Return the highest-scoring candidate
        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0].text
        
        return None
    
    def _detect_tables_with_model(self, doc):
        """
        Use Docling's table model to detect tables in a DoclingDocument.
        
        This is a placeholder implementation - the actual method would depend
        on how the table model works with DoclingDocument.
        """
        # Simplified placeholder
        tables = []
        
        if self.table_model:
            try:
                # This is where you would use the table model with the DoclingDocument
                # The implementation details would depend on the model's requirements
                # For now, we return an empty list
                pass
            except Exception as e:
                logger.error(f"Error using table model: {e}")
        
        return tables
    
    def _convert_docling_table(self, table_data: Dict[str, Any], table_idx: int) -> Optional[TableItem]:
        """
        Convert Docling table representation to a TableItem.
        
        Args:
            table_data: Docling table data
            table_idx: Index of the table
            
        Returns:
            TableItem or None if conversion fails
        """
        try:
            # Extract basic table metadata
            page_idx = table_data.get("page_num", 0) - 1  # Convert 1-based to 0-based
            bbox = table_data.get("bbox", (0, 0, 0, 0))
            confidence = table_data.get("confidence", 0.0)
            
            # Extract structure information
            rows = table_data.get("num_rows", 0)
            cols = table_data.get("num_cols", 0)
            
            # Create TableItem
            table_item = TableItem(
                page_idx=page_idx,
                table_idx=table_idx,
                bbox=bbox,
                rows=rows,
                cols=cols,
                confidence=confidence
            )
            
            # Extract cell data if available
            if self.enable_cell_extraction and "cells" in table_data:
                cells = []
                for cell_data in table_data["cells"]:
                    cell = {
                        "row_idx": cell_data.get("row_idx", 0),
                        "col_idx": cell_data.get("col_idx", 0),
                        "text": cell_data.get("text", ""),
                        "bbox": cell_data.get("bbox", (0, 0, 0, 0)),
                        "rowspan": cell_data.get("rowspan", 1),
                        "colspan": cell_data.get("colspan", 1)
                    }
                    cells.append(cell)
                
                table_item.cells = cells
            
            # Extract caption if available
            if self.enable_caption_detection and "caption" in table_data:
                caption_text = table_data["caption"].get("text", "")
                caption_bbox = table_data["caption"].get("bbox", None)
                table_item.set_caption(caption_text, caption_bbox)
            
            # Add any additional metadata
            if "metadata" in table_data:
                table_item.metadata = table_data["metadata"]
            
            return table_item
        except Exception as e:
            logger.error(f"Error converting Docling table: {e}")
            return None
    
    def _get_pdf_document(self, document: Union[PdfDocument, str, Path, BinaryIO]) -> PdfDocument:
        """
        Get a PdfDocument from various input types.
        
        Args:
            document: PdfDocument, path to PDF file, or file-like object
            
        Returns:
            PdfDocument instance
        """
        from docling_parse.pdf_parser import DoclingPdfParser
        
        if isinstance(document, PdfDocument):
            return document
        
        # Parse the document
        parser = DoclingPdfParser()
        
        if isinstance(document, (str, Path)):
            # Path to PDF file
            return parser.load(path_or_stream=str(document))
        elif hasattr(document, 'read'):
            # File-like object
            return parser.load(path_or_stream=document)
        else:
            raise ValueError(f"Unsupported document type: {type(document)}")
    
    def _detect_tables_basic(self, pdf_doc: PdfDocument) -> List[TableItem]:
        """
        Detect tables using basic heuristics when Docling models are not available.
        
        Args:
            pdf_doc: PdfDocument to analyze
            
        Returns:
            List of TableItem objects representing detected tables
        """
        tables = []
        
        # Process each page in the document
        for page_idx, page in enumerate(pdf_doc.pages):
            # Look for potential table markers in text
            table_sections = self._identify_table_sections(page)
            
            for table_idx, section in enumerate(table_sections):
                start_line, end_line = section["start_line"], section["end_line"]
                table_lines = [page.lines[i].text for i in range(start_line, end_line + 1)]
                
                # Analyze table structure (rows, columns)
                columns = self._analyze_table_columns(table_lines)
                
                # Create a table item
                table_item = TableItem(
                    page_idx=page_idx,
                    table_idx=table_idx,
                    bbox=section.get("bbox", (0, 0, 0, 0)),
                    rows=len(table_lines),
                    cols=columns
                )
                
                # Extract cells
                if self.enable_cell_extraction:
                    cells = self._extract_cells_basic(table_lines, columns)
                    table_item.cells = cells
                
                # Look for caption
                if self.enable_caption_detection:
                    caption = self._find_caption_basic(page, start_line, end_line)
                    if caption:
                        table_item.set_caption(caption.get("text", ""), caption.get("bbox", None))
                
                tables.append(table_item)
        
        return tables
    
    def _identify_table_sections(self, page: Page) -> List[Dict[str, Any]]:
        """
        Identify potential table sections on a page using text patterns.
        
        Args:
            page: Page to analyze
            
        Returns:
            List of dictionaries describing potential table sections
        """
        table_sections = []
        
        if not hasattr(page, 'lines') or not page.lines:
            return []
        
        table_start = None
        in_table = False
        
        # Look for table markers in text
        for i, line in enumerate(page.lines):
            text = line.text.strip()
            
            # Skip empty lines
            if not text:
                continue
            
            # Look for table headers or tabular content
            has_multiple_spaces = len([s for s in text.split('  ') if s.strip()]) >= 3
            has_table_marker = text.lower().startswith(('table ', 'tbl.', 'tab.'))
            
            if not in_table and (has_multiple_spaces or has_table_marker):
                # Potential start of a table
                table_start = i
                in_table = True
            elif in_table and not has_multiple_spaces:
                # Potential end of a table
                table_end = i - 1
                
                # Only consider as table if it spans multiple lines
                if table_start is not None and table_end - table_start >= 2:
                    # Get bounding box of the table
                    x_min, y_min = float('inf'), float('inf')
                    x_max, y_max = 0, 0
                    
                    for j in range(table_start, table_end + 1):
                        if hasattr(page.lines[j], 'bbox'):
                            x0, y0, x1, y1 = page.lines[j].bbox
                            x_min = min(x_min, x0)
                            y_min = min(y_min, y0)
                            x_max = max(x_max, x1)
                            y_max = max(y_max, y1)
                    
                    bbox = (x_min, y_min, x_max, y_max) if x_min != float('inf') else (0, 0, 0, 0)
                    
                    table_sections.append({
                        "start_line": table_start,
                        "end_line": table_end,
                        "bbox": bbox
                    })
                
                # Reset for next table
                table_start = None
                in_table = False
        
        # Handle case where table extends to end of page
        if in_table and table_start is not None:
            table_end = len(page.lines) - 1
            
            # Get bounding box of the table
            x_min, y_min = float('inf'), float('inf')
            x_max, y_max = 0, 0
            
            for j in range(table_start, table_end + 1):
                if hasattr(page.lines[j], 'bbox'):
                    x0, y0, x1, y1 = page.lines[j].bbox
                    x_min = min(x_min, x0)
                    y_min = min(y_min, y0)
                    x_max = max(x_max, x1)
                    y_max = max(y_max, y1)
            
            bbox = (x_min, y_min, x_max, y_max) if x_min != float('inf') else (0, 0, 0, 0)
            
            table_sections.append({
                "start_line": table_start,
                "end_line": table_end,
                "bbox": bbox
            })
        
        return table_sections
    
    def _analyze_table_columns(self, table_lines: List[str]) -> int:
        """
        Analyze table lines to determine the number of columns.
        
        Args:
            table_lines: Lines of text in the table
            
        Returns:
            Estimated number of columns
        """
        column_counts = []
        
        for line in table_lines:
            # Count segments separated by multiple spaces
            segments = [s for s in line.split('  ') if s.strip()]
            if segments:
                column_counts.append(len(segments))
        
        # Use most common column count
        if not column_counts:
            return 0
        
        # Use the mode (most common value)
        return max(set(column_counts), key=column_counts.count)
    
    def _extract_cells_basic(self, table_lines: List[str], columns: int) -> List[Dict[str, Any]]:
        """
        Extract cells from table lines using basic text splitting.
        
        Args:
            table_lines: Lines of text in the table
            columns: Number of columns in the table
            
        Returns:
            List of cell dictionaries
        """
        cells = []
        
        for row_idx, line in enumerate(table_lines):
            # Split line into segments (cells)
            segments = [s.strip() for s in line.split('  ') if s.strip()]
            
            # Adjust to expected number of columns
            if len(segments) < columns:
                segments.extend([""] * (columns - len(segments)))
            elif len(segments) > columns:
                segments = segments[:columns]
            
            # Create cell for each segment
            for col_idx, text in enumerate(segments):
                cell = {
                    "row_idx": row_idx,
                    "col_idx": col_idx,
                    "text": text,
                    "bbox": None,  # Can't determine bbox without more information
                    "rowspan": 1,
                    "colspan": 1
                }
                cells.append(cell)
        
        return cells
    
    def _find_caption_basic(self, page: Page, table_start: int, table_end: int) -> Optional[Dict[str, Any]]:
        """
        Find a table caption near a detected table.
        
        Args:
            page: Page containing the table
            table_start: Starting line index of the table
            table_end: Ending line index of the table
            
        Returns:
            Caption dictionary or None if no caption found
        """
        if not hasattr(page, 'lines') or not page.lines:
            return None
        
        # Look for caption before the table
        caption_line = None
        if table_start > 0:
            line = page.lines[table_start - 1]
            text = line.text.strip().lower()
            if text.startswith(('table ', 'tbl.', 'tab.')):
                caption_line = line
        
        # If not found before, look after the table
        if not caption_line and table_end < len(page.lines) - 1:
            line = page.lines[table_end + 1]
            text = line.text.strip().lower()
            if text.startswith(('table ', 'tbl.', 'tab.')):
                caption_line = line
        
        if caption_line:
            bbox = caption_line.bbox if hasattr(caption_line, 'bbox') else None
            return {
                "text": caption_line.text,
                "bbox": bbox
            }
        
        return None


# Singleton instance for global use
_table_predictor = None


def get_table_predictor(
    table_confidence_threshold: float = 0.5,
    enable_structure_analysis: bool = True,
    enable_cell_extraction: bool = True,
    **kwargs
) -> TablePredictor:
    """
    Get a configured TablePredictor instance.
    
    This is the recommended way to create a TablePredictor with default settings
    or custom configuration.
    
    Args:
        table_confidence_threshold: Minimum confidence for table detection
        enable_structure_analysis: Whether to analyze table structure
        enable_cell_extraction: Whether to extract cell content
        **kwargs: Additional configuration options
        
    Returns:
        Configured TablePredictor instance
        
    Examples:
        # Basic usage with PDF file
        predictor = get_table_predictor()
        tables = predictor.predict("document.pdf")
        
        # Process tables in PdfDocument
        predictor = get_table_predictor(table_confidence_threshold=0.7)
        tables = predictor.predict(pdf_document)
        
        # Process directly with DoclingDocument (preferred native approach)
        predictor = get_table_predictor()
        doc = DoclingDocument(...)  # Your DoclingDocument instance
        updated_doc = predictor.predict_docling(doc)
        
        # Access tables from DoclingDocument
        for table in updated_doc.tables:
            print(f"Table with {table.rows} rows and {table.columns} columns")
    """
    return TablePredictor(
        table_confidence_threshold=table_confidence_threshold,
        enable_structure_analysis=enable_structure_analysis,
        enable_cell_extraction=enable_cell_extraction,
        **kwargs
    )
