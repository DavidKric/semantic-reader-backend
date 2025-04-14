"""
Document structure prediction module that leverages docling's native capabilities.

This module provides functionality to identify document structure elements like
titles, sections, paragraphs, and other semantic components using the native
functionalities of docling, docling-parse, and docling-core.
"""

import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from pathlib import Path
import os

# Import docling document structures
try:
    from docling_core.types import DoclingDocument
    from docling_parse.pdf_parser import PdfDocument
    from docling_core.types.doc.page import SegmentedPage as Page
    from docling.pipeline.simple_pipeline import SimplePipeline as Pipeline
    # Import docling models for structure analysis if available
    try:
        from docling.models.layout_model import LayoutModel
        from docling.models.readingorder_model import ReadingOrderModel
        HAS_DOCLING_MODELS = True
    except ImportError:
        logging.warning("Docling models not found. Using basic structure analysis.")
        HAS_DOCLING_MODELS = False
except ImportError:
    logging.warning("Docling dependencies not found. Structure prediction functionality will be limited.")
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
    
    class Pipeline:
        def __init__(self, *args, **kwargs):
            pass
        
        def process(self, document, **kwargs):
            pass
    
    HAS_DOCLING_MODELS = False

logger = logging.getLogger(__name__)


class StructurePredictor:
    """
    Document structure prediction using docling's native capabilities.
    
    This class leverages docling's models and algorithms to identify 
    document structure elements and semantic components in parsed documents.
    
    It identifies elements such as:
    - Titles and headings
    - Abstracts
    - Paragraphs
    - Lists and bullet points
    - Tables
    - Figures and captions
    - References and footnotes
    """
    
    def __init__(
        self,
        enable_layout_analysis: bool = True,
        enable_table_detection: bool = True,
        layout_confidence_threshold: float = 0.5,
        enable_heading_detection: bool = True,
        custom_models_path: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the structure predictor with configuration options.
        
        Args:
            enable_layout_analysis: Whether to enable layout element detection
            enable_table_detection: Whether to detect and analyze tables
            layout_confidence_threshold: Minimum confidence for layout element detection
            enable_heading_detection: Whether to detect section headings and hierarchy
            custom_models_path: Path to custom docling models (if any)
            **kwargs: Additional configuration options
        """
        self.enable_layout_analysis = enable_layout_analysis
        self.enable_table_detection = enable_table_detection
        self.layout_confidence_threshold = layout_confidence_threshold
        self.enable_heading_detection = enable_heading_detection
        self.custom_models_path = custom_models_path
        self.config = kwargs
        
        logger.info(
            f"Initializing StructurePredictor (layout analysis: {enable_layout_analysis}, "
            f"table detection: {enable_table_detection}, "
            f"heading detection: {enable_heading_detection})"
        )
        
        # Initialize docling models if available
        self.layout_analyzer = None
        self.structure_analyzer = None
        
        if HAS_DOCLING_MODELS:
            try:
                # Initialize docling's native layout analyzer
                self.layout_analyzer = LayoutModel(
                    confidence_threshold=layout_confidence_threshold,
                    model_path=custom_models_path
                )
                logger.info("Successfully initialized docling LayoutModel")
                
                # Initialize docling's native structure analyzer for hierarchical structure
                self.structure_analyzer = ReadingOrderModel(
                    enable_heading_detection=enable_heading_detection
                )
                logger.info("Successfully initialized docling ReadingOrderModel")
            except Exception as e:
                logger.error(f"Failed to initialize docling models: {e}")
        else:
            logger.warning(
                "Docling models not available. "
                "Using basic structure detection with limited capabilities."
            )
        
        # Initialize docling pipeline for document processing
        try:
            self.pipeline = Pipeline()
            logger.info("Successfully initialized docling Pipeline")
        except Exception as e:
            logger.error(f"Failed to initialize docling Pipeline: {e}")
            self.pipeline = None
    
    def apply(self, document: Union[PdfDocument, DoclingDocument], **kwargs) -> None:
        """
        Apply structure prediction to a document.
        
        This method identifies document structure elements and adds them
        to the document's entity layers.
        
        Args:
            document: Docling document to analyze
            **kwargs: Additional processing options
        
        Returns:
            None (modifies document in-place)
        """
        logger.info("Starting structure prediction on document")
        
        if not document or not hasattr(document, 'pages'):
            logger.error("Invalid document or no pages found")
            return
        
        # Process document using docling's pipeline if available
        if self.pipeline and HAS_DOCLING_MODELS:
            try:
                logger.info("Processing document with docling pipeline")
                self.pipeline.process(document, **kwargs)
                logger.info("Document successfully processed with docling pipeline")
                return
            except Exception as e:
                logger.warning(f"Error in docling pipeline processing: {e}. Falling back to manual processing.")
        
        # Manual processing if pipeline or models are not available
        self._process_document_structure(document)
    
    def _process_document_structure(self, document: Union[PdfDocument, DoclingDocument]) -> None:
        """
        Process document structure manually when docling pipeline is not available.
        
        Args:
            document: Document to analyze
        """
        logger.info("Processing document structure manually")
        
        # Initialize metadata structure if needed
        if not hasattr(document, 'metadata'):
            document.metadata = {}
        
        # Process structure at document level
        document.metadata['structure_analyzed'] = True
        
        # Process each page
        for page_idx, page in enumerate(document.pages):
            logger.debug(f"Processing structure for page {page_idx+1}")
            
            # Extract structural elements
            try:
                titles = self._extract_titles(page)
                paragraphs = self._extract_paragraphs(page)
                headings = self._extract_headings(page) if self.enable_heading_detection else []
                tables = self._extract_tables(page) if self.enable_table_detection else []
                
                # Store structure information in page metadata
                if not hasattr(page, 'metadata'):
                    page.metadata = {}
                
                page.metadata.update({
                    'has_title': bool(titles),
                    'has_paragraphs': bool(paragraphs),
                    'has_headings': bool(headings),
                    'has_tables': bool(tables),
                    'structure_elements': {
                        'titles': len(titles),
                        'paragraphs': len(paragraphs),
                        'headings': len(headings),
                        'tables': len(tables)
                    }
                })
                
                logger.debug(f"Identified structure elements on page {page_idx+1}: "
                            f"titles={len(titles)}, paragraphs={len(paragraphs)}, "
                            f"headings={len(headings)}, tables={len(tables)}")
            except Exception as e:
                logger.error(f"Error analyzing structure on page {page_idx+1}: {e}")
        
        logger.info("Completed manual document structure processing")
    
    def _extract_titles(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extract titles from page using heuristic rules.
        
        Args:
            page: Page to analyze
            
        Returns:
            List of detected titles with metadata
        """
        titles = []
        
        # Simple heuristic: first few lines might be titles
        # In a real implementation, we would use font size, position, etc.
        if hasattr(page, 'lines') and page.lines:
            for i, line in enumerate(page.lines[:3]):  # Check first 3 lines
                if not line.text.strip():
                    continue
                
                # Simple title detection: shorter lines at the top of the page
                # with fewer than 10 words might be titles
                words = line.text.strip().split()
                if len(words) < 10:
                    titles.append({
                        'text': line.text,
                        'line_index': i,
                        'confidence': 0.7 if i == 0 else 0.5,
                        'type': 'main_title' if i == 0 else 'subtitle'
                    })
        
        return titles
    
    def _extract_paragraphs(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extract paragraphs from page using line grouping.
        
        Args:
            page: Page to analyze
            
        Returns:
            List of detected paragraphs with metadata
        """
        paragraphs = []
        current_paragraph = []
        
        if hasattr(page, 'lines') and page.lines:
            for i, line in enumerate(page.lines):
                if not line.text.strip():
                    # Empty line might indicate paragraph break
                    if current_paragraph:
                        paragraphs.append({
                            'text': '\n'.join(current_paragraph),
                            'line_indices': list(range(i - len(current_paragraph), i)),
                            'confidence': 0.8
                        })
                        current_paragraph = []
                else:
                    current_paragraph.append(line.text)
            
            # Add final paragraph if exists
            if current_paragraph:
                paragraphs.append({
                    'text': '\n'.join(current_paragraph),
                    'line_indices': list(range(len(page.lines) - len(current_paragraph), len(page.lines))),
                    'confidence': 0.8
                })
        
        return paragraphs
    
    def _extract_headings(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extract section headings from page.
        
        Args:
            page: Page to analyze
            
        Returns:
            List of detected headings with metadata
        """
        headings = []
        
        if hasattr(page, 'lines') and page.lines:
            for i, line in enumerate(page.lines):
                text = line.text.strip()
                if not text:
                    continue
                
                # Simple heading detection: lines starting with numbers or certain patterns
                if (text.startswith(('1.', '2.', '3.', '4.', '5.', 'I.', 'II.', 'III.')) or
                    text.lower().startswith(('introduction', 'abstract', 'background', 
                                             'method', 'result', 'discussion', 'conclusion'))):
                    headings.append({
                        'text': text,
                        'line_index': i,
                        'confidence': 0.6,
                        'level': 1 if any(text.lower().startswith(h) for h in 
                                          ('abstract', 'introduction', 'conclusion')) else 2
                    })
        
        return headings
    
    def _extract_tables(self, page: Page) -> List[Dict[str, Any]]:
        """
        Extract tables from page.
        
        Args:
            page: Page to analyze
            
        Returns:
            List of detected tables with metadata
        """
        tables = []
        
        # Table detection would normally require docling's dedicated table models
        # This is a simple placeholder that looks for potential tabular content
        if hasattr(page, 'lines') and page.lines:
            table_start_idx = None
            for i, line in enumerate(page.lines):
                text = line.text.strip()
                
                # Check if line might be a table row (has multiple whitespace-separated segments)
                segments = [s for s in text.split('  ') if s.strip()]
                if len(segments) >= 3:  # Potential table row with at least 3 columns
                    if table_start_idx is None:
                        table_start_idx = i
                else:
                    # End of potential table
                    if table_start_idx is not None and i - table_start_idx > 2:
                        # At least 3 rows to consider it a table
                        tables.append({
                            'start_line': table_start_idx,
                            'end_line': i - 1,
                            'num_rows': i - table_start_idx,
                            'confidence': 0.5
                        })
                    table_start_idx = None
            
            # Check for table at end of page
            if table_start_idx is not None and len(page.lines) - table_start_idx > 2:
                tables.append({
                    'start_line': table_start_idx,
                    'end_line': len(page.lines) - 1,
                    'num_rows': len(page.lines) - table_start_idx,
                    'confidence': 0.5
                })
        
        return tables


# Singleton instance for global use
_structure_predictor = None


def get_structure_predictor(
    enable_layout_analysis: bool = True,
    enable_table_detection: bool = True,
    **kwargs
) -> StructurePredictor:
    """
    Get or create a singleton instance of StructurePredictor.
    
    Args:
        enable_layout_analysis: Whether to enable layout element detection
        enable_table_detection: Whether to detect and analyze tables
        **kwargs: Additional configuration options
        
    Returns:
        Singleton instance of StructurePredictor
    """
    global _structure_predictor
    if _structure_predictor is None:
        _structure_predictor = StructurePredictor(
            enable_layout_analysis=enable_layout_analysis,
            enable_table_detection=enable_table_detection,
            **kwargs
        )
    return _structure_predictor
