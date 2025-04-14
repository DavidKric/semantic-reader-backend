from typing import Dict, List, Any, Optional, Union, Tuple
import logging
from pathlib import Path
import json

# Import Docling document structures
try:
    from docling_core.types import DoclingDocument
    from docling_parse.pdf_parser import PdfDocument
    from docling_core.types.doc import TextItem, TableItem, PictureItem, KeyValueItem
except ImportError:
    logging.warning("Docling dependencies not found. Some conversion features may not work.")
    # Define stub classes for type hints
    class DoclingDocument:
        pass
    
    class PdfDocument:
        pass
    
    class TextItem:
        pass
    
    class TableItem:
        pass
    
    class PictureItem:
        pass
    
    class KeyValueItem:
        pass

# Import our PaperMage document structure
from .document import Document, Entity, Span, Box

logger = logging.getLogger(__name__)


class DoclingToPaperMageConverter:
    """
    Converts Docling document structures to PaperMage compatible format.
    
    This converter acts as a bridge between Docling's native document 
    representations and PaperMage's expected format.
    """
    
    @staticmethod
    def convert_pdf_document(pdf_doc: PdfDocument) -> Document:
        """
        Convert a Docling PdfDocument to a PaperMage-compatible Document.
        
        Args:
            pdf_doc: A PdfDocument instance from docling_parse
            
        Returns:
            A PaperMage-compatible Document instance
        """
        # Create a new Document
        doc = Document()
        
        # Start with empty symbols
        full_text = ""
        
        # Process pages
        pages = []
        tokens = []
        words = []
        rows = []
        
        current_position = 0
        
        # Get page count
        num_pages = pdf_doc.number_of_pages() if hasattr(pdf_doc, 'number_of_pages') else 0
        
        # Iterate through pages
        for page_idx, page in pdf_doc.iterate_pages():
            page_start = current_position
            page_text = ""
            
            # Get page dimensions from page if available
            page_width = 612  # Default Letter width
            page_height = 792  # Default Letter height
            
            if hasattr(page, 'dimension'):
                if hasattr(page.dimension, 'width'):
                    page_width = page.dimension.width
                if hasattr(page.dimension, 'height'):
                    page_height = page.dimension.height
            
            # Process textline cells - these are our "rows"
            if hasattr(page, 'textline_cells') and page.textline_cells:
                for cell in page.textline_cells:
                    # Skip cells without text
                    if not hasattr(cell, 'text') or not cell.text:
                        continue
                    
                    line_text = cell.text
                    line_start = current_position
                    
                    # Add to full text
                    page_text += line_text + "\n"
                    current_position += len(line_text) + 1  # +1 for newline
                    
                    # Get bounding box information
                    line_bbox_x0 = 0
                    line_bbox_y0 = 0
                    line_bbox_x1 = page_width
                    line_bbox_y1 = 20  # Default height
                    
                    if hasattr(cell, 'rect'):
                        line_bbox_x0 = cell.rect.x0 if hasattr(cell.rect, 'x0') else 0
                        line_bbox_y0 = cell.rect.y0 if hasattr(cell.rect, 'y0') else 0
                        line_bbox_x1 = cell.rect.x1 if hasattr(cell.rect, 'x1') else page_width
                        line_bbox_y1 = cell.rect.y1 if hasattr(cell.rect, 'y1') else (line_bbox_y0 + 20)
                    
                    # Create row entity
                    row_span = Span(start=line_start, end=current_position - 1)
                    row_box = Box(
                        x0=line_bbox_x0, 
                        y0=line_bbox_y0,
                        x1=line_bbox_x1,
                        y1=line_bbox_y1,
                        page=page_idx
                    )
                    
                    # Add metadata for right-to-left text if detected
                    row_metadata = {}
                    if hasattr(cell, 'left_to_right') and not cell.left_to_right:
                        row_metadata["is_rtl"] = True
                    
                    rows.append(Entity(spans=[row_span], boxes=[row_box], text=line_text, metadata=row_metadata))
            
            # Process word cells
            if hasattr(page, 'word_cells') and page.word_cells:
                for cell in page.word_cells:
                    # Skip cells without text
                    if not hasattr(cell, 'text') or not cell.text:
                        continue
                    
                    word_text = cell.text
                    
                    # Find position of this word in the full text
                    word_pos = page_text.find(word_text)
                    if word_pos != -1:
                        word_start = page_start + word_pos
                        word_end = word_start + len(word_text) - 1
                        
                        # Get bounding box information
                        word_bbox_x0 = 0
                        word_bbox_y0 = 0
                        word_bbox_x1 = 100  # Default width
                        word_bbox_y1 = 20   # Default height
                        
                        if hasattr(cell, 'rect'):
                            word_bbox_x0 = cell.rect.x0 if hasattr(cell.rect, 'x0') else 0
                            word_bbox_y0 = cell.rect.y0 if hasattr(cell.rect, 'y0') else 0
                            word_bbox_x1 = cell.rect.x1 if hasattr(cell.rect, 'x1') else word_bbox_x0 + 100
                            word_bbox_y1 = cell.rect.y1 if hasattr(cell.rect, 'y1') else word_bbox_y0 + 20
                        
                        word_span = Span(start=word_start, end=word_end)
                        word_box = Box(
                            x0=word_bbox_x0,
                            y0=word_bbox_y0,
                            x1=word_bbox_x1,
                            y1=word_bbox_y1,
                            page=page_idx
                        )
                        
                        # Add metadata for right-to-left text if detected
                        word_metadata = {}
                        if hasattr(cell, 'left_to_right') and not cell.left_to_right:
                            word_metadata["is_rtl"] = True
                        
                        # Add as both word and token for compatibility
                        words.append(Entity(spans=[word_span], boxes=[word_box], text=word_text, metadata=word_metadata))
                        tokens.append(Entity(spans=[word_span], boxes=[word_box], text=word_text, metadata=word_metadata))
            
            # Create page entity
            page_end = current_position - 1
            page_span = Span(start=page_start, end=page_end)
            page_box = Box(
                x0=0,
                y0=0,
                x1=page_width,
                y1=page_height,
                page=page_idx
            )
            pages.append(Entity(spans=[page_span], boxes=[page_box]))
            
            # Add page text to full document text
            full_text += page_text
        
        # Populate the document
        doc.symbols = full_text
        
        # Add all entity layers
        doc.add_entity_layer("pages", pages)
        doc.add_entity_layer("rows", rows)
        doc.add_entity_layer("tokens", tokens)
        doc.add_entity_layer("words", words)
        
        # Add metadata, including RTL detection information
        doc.metadata = {
            "filename": pdf_doc.filename if hasattr(pdf_doc, "filename") else "",
            "num_pages": num_pages,
            "version": "0.1.0"
        }
        
        # Copy RTL detection metadata
        if hasattr(pdf_doc, 'metadata'):
            for key, value in pdf_doc.metadata.items():
                doc.metadata[key] = value
        
        return doc
    
    @staticmethod
    def convert_docling_document(docling_doc: DoclingDocument) -> Document:
        """
        Convert a DoclingDocument to a PaperMage-compatible Document.
        
        Args:
            docling_doc: A DoclingDocument instance from docling_core
            
        Returns:
            A PaperMage-compatible Document instance
        """
        logger.info("Converting DoclingDocument to PaperMage format")
        
        # Create a new Document
        doc = Document()
        
        # Initialize entity layers
        pages = []
        paragraphs = []
        sentences = []
        words = []
        tokens = []
        rows = []
        blocks = []
        figures = []
        tables = []
        bibliography_entries = []
        citations = []
        equations = []
        
        # Extract full text and track position
        full_text = ""
        current_position = 0
        
        # Process metadata
        doc.metadata = {
            "source": "docling",
            "version": "0.18.0",  # Match PaperMage v0.18+ as specified in PRD
        }
        
        # Copy over document metadata if available
        if hasattr(docling_doc, "metadata"):
            for key, value in docling_doc.metadata.items():
                doc.metadata[key] = value
        
        # Extract document title if available
        if hasattr(docling_doc, "title"):
            doc.metadata["title"] = docling_doc.title
        
        # Track the bibliography section for citation matching
        bibliography_section_detected = False
        
        # Process each page
        if hasattr(docling_doc, "pages"):
            for page_idx, page in enumerate(docling_doc.pages):
                page_start = current_position
                page_text = ""
                
                # Create page entity
                if hasattr(page, "width") and hasattr(page, "height"):
                    page_box = Box(
                        x0=0,
                        y0=0,
                        x1=page.width,
                        y1=page.height,
                        page=page_idx
                    )
                else:
                    # Default page dimensions if not available
                    page_box = Box(
                        x0=0,
                        y0=0,
                        x1=612,  # Letter size default in points
                        y1=792,
                        page=page_idx
                    )
                
                # Process page content
                if hasattr(page, "content"):
                    for item in page.content:
                        # Process text items
                        if isinstance(item, TextItem):
                            item_text = item.text if hasattr(item, "text") else ""
                            item_start = current_position
                            
                            # Check for bibliography header
                            if not bibliography_section_detected and item_text.lower().strip() in [
                                "references", "bibliography", "works cited"
                            ]:
                                bibliography_section_detected = True
                                doc.metadata["has_bibliography"] = True
                            
                            # Add to full text
                            page_text += item_text + "\n"
                            current_position += len(item_text) + 1  # +1 for newline
                            
                            # Create bounding box for the text item
                            if hasattr(item, "bbox"):
                                item_box = Box(
                                    x0=item.bbox.x0,
                                    y0=item.bbox.y0,
                                    x1=item.bbox.x1,
                                    y1=item.bbox.y1,
                                    page=page_idx
                                )
                            else:
                                # Default bounding box if not available
                                item_box = Box(
                                    x0=0,
                                    y0=0,
                                    x1=100,
                                    y1=100,
                                    page=page_idx
                                )
                            
                            # Create text span
                            item_span = Span(start=item_start, end=current_position - 1)
                            
                            # Determine text item type and add to appropriate layer
                            if hasattr(item, "category"):
                                if item.category == "paragraph":
                                    paragraphs.append(Entity(spans=[item_span], boxes=[item_box], text=item_text))
                                    blocks.append(Entity(spans=[item_span], boxes=[item_box], text=item_text))
                                elif item.category == "heading":
                                    # Add heading-specific metadata
                                    blocks.append(Entity(
                                        spans=[item_span], 
                                        boxes=[item_box], 
                                        text=item_text, 
                                        metadata={"is_heading": True, "level": item.level if hasattr(item, "level") else 1}
                                    ))
                                elif item.category == "equation":
                                    equations.append(Entity(spans=[item_span], boxes=[item_box], text=item_text))
                                elif bibliography_section_detected and item.category == "reference":
                                    bibliography_entries.append(Entity(spans=[item_span], boxes=[item_box], text=item_text))
                                else:
                                    # Default to block for other categories
                                    blocks.append(Entity(spans=[item_span], boxes=[item_box], text=item_text))
                            else:
                                # Default to block if no category
                                blocks.append(Entity(spans=[item_span], boxes=[item_box], text=item_text))
                            
                            # Process sentences if available
                            if hasattr(item, "sentences"):
                                sentence_position = item_start
                                for sentence in item.sentences:
                                    sentence_text = sentence.text if hasattr(sentence, "text") else ""
                                    sentence_start = sentence_position
                                    sentence_end = sentence_start + len(sentence_text)
                                    sentence_position = sentence_end + 1  # +1 for space
                                    
                                    # Create sentence bounding box
                                    if hasattr(sentence, "bbox"):
                                        sentence_box = Box(
                                            x0=sentence.bbox.x0,
                                            y0=sentence.bbox.y0,
                                            x1=sentence.bbox.x1,
                                            y1=sentence.bbox.y1,
                                            page=page_idx
                                        )
                                    else:
                                        # Inherit from parent if not available
                                        sentence_box = item_box
                                    
                                    sentence_span = Span(start=sentence_start, end=sentence_end)
                                    sentences.append(Entity(spans=[sentence_span], boxes=[sentence_box], text=sentence_text))
                                    
                                    # Check for citations in the sentence
                                    # Simple regex-based detection for common citation formats
                                    if "[" in sentence_text and "]" in sentence_text:
                                        import re
                                        citation_matches = re.finditer(r'\[(\d+(?:,\s*\d+)*)\]', sentence_text)
                                        for match in citation_matches:
                                            citation_text = match.group(0)
                                            citation_start = sentence_start + match.start()
                                            citation_end = sentence_start + match.end()
                                            citation_span = Span(start=citation_start, end=citation_end)
                                            
                                            # Create citation entity
                                            citations.append(Entity(
                                                spans=[citation_span], 
                                                boxes=[sentence_box],  # Inherit from sentence since we don't have exact coordinates
                                                text=citation_text,
                                                metadata={
                                                    "citation_ids": match.group(1).split(','),
                                                    "type": "numerical"
                                                }
                                            ))
                            
                            # Process words/tokens if available
                            if hasattr(item, "words"):
                                word_position = item_start
                                for word in item.words:
                                    word_text = word.text if hasattr(word, "text") else ""
                                    word_start = word_position
                                    word_end = word_start + len(word_text)
                                    word_position = word_end + 1  # +1 for space
                                    
                                    # Create word bounding box
                                    if hasattr(word, "bbox"):
                                        word_box = Box(
                                            x0=word.bbox.x0,
                                            y0=word.bbox.y0,
                                            x1=word.bbox.x1,
                                            y1=word.bbox.y1,
                                            page=page_idx
                                        )
                                    else:
                                        # Inherit from parent if not available
                                        word_box = item_box
                                    
                                    word_span = Span(start=word_start, end=word_end)
                                    
                                    # Add as both word and token for compatibility with PaperMage
                                    words.append(Entity(spans=[word_span], boxes=[word_box], text=word_text))
                                    tokens.append(Entity(spans=[word_span], boxes=[word_box], text=word_text))
                        
                        # Process table items
                        elif isinstance(item, TableItem):
                            table_start = current_position
                            
                            # Extract table text representation if possible
                            table_text = item.text if hasattr(item, "text") else "Table content"
                            
                            # Add to full text
                            page_text += table_text + "\n"
                            current_position += len(table_text) + 1  # +1 for newline
                            
                            # Create bounding box for the table
                            if hasattr(item, "bbox"):
                                table_box = Box(
                                    x0=item.bbox.x0,
                                    y0=item.bbox.y0,
                                    x1=item.bbox.x1,
                                    y1=item.bbox.y1,
                                    page=page_idx
                                )
                            else:
                                # Default bounding box if not available
                                table_box = Box(
                                    x0=0,
                                    y0=0,
                                    x1=100,
                                    y1=100,
                                    page=page_idx
                                )
                            
                            # Create table span
                            table_span = Span(start=table_start, end=current_position - 1)
                            
                            # Create table structure metadata
                            table_metadata = {
                                "num_rows": item.num_rows if hasattr(item, "num_rows") else 0,
                                "num_cols": item.num_cols if hasattr(item, "num_cols") else 0,
                                "has_header": item.has_header if hasattr(item, "has_header") else False
                            }
                            
                            # Process table cells if available
                            if hasattr(item, "cells"):
                                table_metadata["cells"] = []
                                for cell in item.cells:
                                    cell_data = {
                                        "text": cell.text if hasattr(cell, "text") else "",
                                        "row": cell.row if hasattr(cell, "row") else 0,
                                        "col": cell.col if hasattr(cell, "col") else 0,
                                        "rowspan": cell.rowspan if hasattr(cell, "rowspan") else 1,
                                        "colspan": cell.colspan if hasattr(cell, "colspan") else 1
                                    }
                                    
                                    # Add bounding box if available
                                    if hasattr(cell, "bbox"):
                                        cell_data["bbox"] = {
                                            "x0": cell.bbox.x0,
                                            "y0": cell.bbox.y0,
                                            "x1": cell.bbox.x1,
                                            "y1": cell.bbox.y1
                                        }
                                    
                                    table_metadata["cells"].append(cell_data)
                            
                            # Add table entity
                            tables.append(Entity(
                                spans=[table_span],
                                boxes=[table_box],
                                text=table_text,
                                metadata=table_metadata
                            ))
                            
                            # Tables are also blocks
                            blocks.append(Entity(
                                spans=[table_span],
                                boxes=[table_box],
                                text=table_text,
                                metadata={"is_table": True}
                            ))
                        
                        # Process picture/figure items
                        elif isinstance(item, PictureItem):
                            figure_start = current_position
                            
                            # Extract figure caption if available
                            caption_text = item.caption if hasattr(item, "caption") else "Figure"
                            
                            # Add to full text
                            page_text += caption_text + "\n"
                            current_position += len(caption_text) + 1  # +1 for newline
                            
                            # Create bounding box for the figure
                            if hasattr(item, "bbox"):
                                figure_box = Box(
                                    x0=item.bbox.x0,
                                    y0=item.bbox.y0,
                                    x1=item.bbox.x1,
                                    y1=item.bbox.y1,
                                    page=page_idx
                                )
                            else:
                                # Default bounding box if not available
                                figure_box = Box(
                                    x0=0,
                                    y0=0,
                                    x1=100,
                                    y1=100,
                                    page=page_idx
                                )
                            
                            # Create figure span
                            figure_span = Span(start=figure_start, end=current_position - 1)
                            
                            # Create figure metadata
                            figure_metadata = {
                                "has_caption": hasattr(item, "caption"),
                                "figure_type": item.figure_type if hasattr(item, "figure_type") else "image"
                            }
                            
                            # Add figure entity
                            figures.append(Entity(
                                spans=[figure_span],
                                boxes=[figure_box],
                                text=caption_text,
                                metadata=figure_metadata
                            ))
                            
                            # Figures are also blocks
                            blocks.append(Entity(
                                spans=[figure_span],
                                boxes=[figure_box],
                                text=caption_text,
                                metadata={"is_figure": True}
                            ))
                
                # Add page text to full document text
                full_text += page_text
                
                # Create page span
                page_end = current_position - 1
                page_span = Span(start=page_start, end=page_end)
                
                # Add page entity
                pages.append(Entity(spans=[page_span], boxes=[page_box]))
        
        # Set full document text
        doc.symbols = full_text
        
        # Add entity layers to the document
        doc.add_entity_layer("pages", pages)
        doc.add_entity_layer("paragraphs", paragraphs)
        doc.add_entity_layer("sentences", sentences)
        doc.add_entity_layer("words", words)
        doc.add_entity_layer("tokens", tokens)
        doc.add_entity_layer("blocks", blocks)
        
        # Only add non-empty layers
        if rows:
            doc.add_entity_layer("rows", rows)
        if figures:
            doc.add_entity_layer("figures", figures)
        if tables:
            doc.add_entity_layer("tables", tables)
        if bibliography_entries:
            doc.add_entity_layer("bibliography", bibliography_entries)
        if citations:
            doc.add_entity_layer("citations", citations)
        if equations:
            doc.add_entity_layer("equations", equations)
        
        # Validate JSON format matches PaperMage v0.18+
        try:
            json_output = doc.to_json()
            logger.info(f"Successfully converted DoclingDocument to PaperMage format with {len(doc.entities)} entity layers")
        except Exception as e:
            logger.error(f"Error validating PaperMage JSON format: {e}")
            raise
        
        return doc
    
    @staticmethod
    def validate_papermage_format(document: Document) -> bool:
        """
        Validate that the document structure matches PaperMage's expected format.
        
        Args:
            document: Document to validate
            
        Returns:
            True if validation succeeds, raises exception otherwise
        """
        required_fields = ["symbols", "entities", "metadata"]
        for field in required_fields:
            if not hasattr(document, field):
                raise ValueError(f"Missing required field: {field}")
        
        # Validate JSON serialization
        try:
            json_output = document.to_json()
            # Check for minimal required structure
            if "symbols" not in json_output or "entities" not in json_output or "metadata" not in json_output:
                raise ValueError("Invalid PaperMage JSON structure")
            
            return True
        except Exception as e:
            logger.error(f"PaperMage format validation failed: {e}")
            raise ValueError(f"PaperMage format validation failed: {e}")
    
    @staticmethod
    def convert_v2_document(docling_doc: Dict) -> Document:
        """
        Convert a Docling V2 document dictionary to a PaperMage-compatible Document.
        
        Args:
            docling_doc: A dictionary containing Docling V2 parser output
            
        Returns:
            A PaperMage-compatible Document instance
        """
        logger.info("Converting Docling V2 document to PaperMage format")
        
        # Create a new Document
        doc = Document()
        
        # Start with empty symbols
        full_text = ""
        
        # Process pages
        pages = []
        tokens = []
        words = []
        rows = []
        
        current_position = 0
        
        # Get metadata
        metadata = docling_doc.get("metadata", {})
        num_pages = metadata.get("num_pages", 0)
        
        # Process each page
        for page_info in docling_doc.get("pages", []):
            page_idx = page_info.get("page_number", 1) - 1  # Convert to 0-indexed
            page_start = current_position
            page_text = ""
            
            # Default page dimensions
            page_width = 612  # Default Letter width
            page_height = 792  # Default Letter height
            
            # Extract page data
            page_data = page_info.get("data", {})
            
            # Process pages from data
            page_entries = page_data.get("pages", [])
            if page_entries:
                page = page_entries[0]  # Get first page entry
                
                # Get sanitized cells data
                if "sanitized" in page and "cells" in page["sanitized"]:
                    cells = page["sanitized"]["cells"]
                    header = cells.get("header", [])
                    data = cells.get("data", [])
                    
                    # Find indices for important columns
                    text_idx = header.index("text") if "text" in header else -1
                    rtl_idx = header.index("left_to_right") if "left_to_right" in header else -1
                    
                    # Process cells as rows
                    row_number = 0
                    for cell in data:
                        if text_idx >= 0 and text_idx < len(cell) and cell[text_idx]:
                            line_text = cell[text_idx]
                            is_rtl = False
                            
                            # Check if RTL
                            if rtl_idx >= 0 and rtl_idx < len(cell):
                                is_rtl = cell[rtl_idx] == 0  # 0 means RTL in Docling
                            
                            line_start = current_position
                            
                            # Add to full text
                            page_text += line_text + "\n"
                            current_position += len(line_text) + 1  # +1 for newline
                            
                            # Create row span
                            row_span = Span(start=line_start, end=current_position - 1)
                            
                            # Create row box (default values since cell coordinates aren't provided)
                            row_box = Box(
                                x0=0,
                                y0=row_number * 15,  # Approximate vertical position
                                x1=page_width,
                                y1=(row_number + 1) * 15,
                                page=page_idx
                            )
                            
                            # Add row metadata
                            row_metadata = {}
                            if is_rtl:
                                row_metadata["is_rtl"] = True
                            
                            # Add row entity
                            rows.append(Entity(
                                spans=[row_span],
                                boxes=[row_box],
                                text=line_text,
                                metadata=row_metadata
                            ))
                            
                            # Extract words from the line
                            word_offset = 0
                            for word in line_text.split():
                                if not word:
                                    continue
                                    
                                # Find exact position in the line
                                while line_text[word_offset:].strip().find(word) != 0:
                                    word_offset += 1
                                    if word_offset >= len(line_text):
                                        break
                                
                                if word_offset >= len(line_text):
                                    continue
                                    
                                word_start = line_start + word_offset
                                word_end = word_start + len(word)
                                word_offset = word_end
                                
                                # Create word span
                                word_span = Span(start=word_start, end=word_end - 1)
                                
                                # Create word box (approximate position)
                                word_box = Box(
                                    x0=0,  # We don't have exact x-coordinates
                                    y0=row_number * 15,
                                    x1=100,
                                    y1=(row_number + 1) * 15,
                                    page=page_idx
                                )
                                
                                # Add word metadata
                                word_metadata = {}
                                if is_rtl:
                                    word_metadata["is_rtl"] = True
                                
                                # Add as both word and token
                                words.append(Entity(
                                    spans=[word_span],
                                    boxes=[word_box],
                                    text=word,
                                    metadata=word_metadata
                                ))
                                
                                tokens.append(Entity(
                                    spans=[word_span],
                                    boxes=[word_box],
                                    text=word,
                                    metadata=word_metadata
                                ))
                            
                            row_number += 1
            
            # Create page entity
            page_end = current_position - 1
            page_span = Span(start=page_start, end=page_end)
            page_box = Box(
                x0=0,
                y0=0,
                x1=page_width,
                y1=page_height,
                page=page_idx
            )
            pages.append(Entity(spans=[page_span], boxes=[page_box]))
            
            # Add page text to full document text
            full_text += page_text
        
        # Set full document text
        doc.symbols = full_text
        
        # Add all entity layers
        doc.add_entity_layer("pages", pages)
        doc.add_entity_layer("rows", rows)
        doc.add_entity_layer("tokens", tokens)
        doc.add_entity_layer("words", words)
        
        # Add metadata
        doc.metadata = {
            "num_pages": num_pages,
            "version": "0.1.0",
            "parser": "docling_v2"
        }
        
        # Copy RTL metadata
        if metadata.get("has_rtl"):
            doc.metadata["has_rtl"] = True
            doc.metadata["rtl_lines_count"] = metadata.get("rtl_lines_count", 0)
        
        # Copy language metadata
        if "language" in metadata:
            doc.metadata["language"] = metadata["language"]
        if "language_name" in metadata:
            doc.metadata["language_name"] = metadata["language_name"]
        if "is_rtl_language" in metadata:
            doc.metadata["is_rtl_language"] = metadata["is_rtl_language"]
        
        return doc 