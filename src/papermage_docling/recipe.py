"""
Recipe module for document processing.

This module provides recipe-based document processing similar to PaperMage's
CoreRecipe, but powered by Docling's document parsing and prediction capabilities.
"""

import logging
import os
from typing import Dict, List, Any, Optional, Union, BinaryIO
from pathlib import Path

from papermage_docling.pipeline.simple_pipeline import SimplePipeline

logger = logging.getLogger(__name__)

class CoreRecipe:
    """
    Recipe for document processing similar to PaperMage's CoreRecipe.
    
    This class provides a convenient interface for processing documents
    using Docling's document parsing and prediction capabilities, with
    an API similar to PaperMage's CoreRecipe for easy migration.
    """
    
    def __init__(
        self,
        enable_ocr: bool = False,
        ocr_language: str = "eng",
        detect_rtl: bool = True,
        detect_tables: bool = True,
        detect_figures: bool = True,
        detect_equations: bool = True,
        detect_sections: bool = True,
        **kwargs
    ):
        """
        Initialize the document processing recipe.
        
        Args:
            enable_ocr: Whether to use OCR for text extraction
            ocr_language: Language to use for OCR
            detect_rtl: Whether to detect and process RTL text
            detect_tables: Whether to detect tables
            detect_figures: Whether to detect figures
            detect_equations: Whether to detect equations
            detect_sections: Whether to detect document sections
            **kwargs: Additional configuration options
        """
        self.config = {
            "enable_ocr": enable_ocr,
            "ocr_language": ocr_language,
            "detect_rtl": detect_rtl,
            "detect_tables": detect_tables,
            "detect_figures": detect_figures,
            "detect_equations": detect_equations,
            "detect_sections": detect_sections,
            **kwargs
        }
        
        # Create the pipeline
        self.pipeline = SimplePipeline.create_default_pipeline()
        logger.info("Initialized CoreRecipe with default pipeline")
    
    def run(self, document: Union[str, bytes, BinaryIO, Path]) -> Any:
        """
        Process a document using the recipe.
        
        This is the main entry point for document processing, similar to
        PaperMage's CoreRecipe.run() method.
        
        Args:
            document: Document to process (file path, bytes, or file-like object)
            
        Returns:
            Processed document in PaperMage-compatible format
        """
        logger.info(f"Processing document with CoreRecipe")
        
        # Handle different input types
        if isinstance(document, (str, Path)):
            # Process file path
            doc = self.pipeline.process_file(str(document), **self.config)
        elif isinstance(document, (bytes, BinaryIO)):
            # Import document parsing functionality
            from papermage_docling.parsers import DoclingPdfParser
            
            # Create parser with config options
            parser = DoclingPdfParser(**self.config)
            
            # Parse bytes or file-like object
            if isinstance(document, bytes):
                doc_dict = parser.parse_bytes(document)
            else:
                content = document.read()
                doc_dict = parser.parse_bytes(content)
                
            # Convert to DoclingDocument and process
            from papermage_docling.api.adapters.factory import convert_document
            doc = convert_document(doc_dict, "papermage", "docling")
            
            # Process through pipeline
            doc = self.pipeline.process(doc, **self.config)
        else:
            raise ValueError(f"Unsupported document type: {type(document)}")
        
        # Convert back to PaperMage format
        return self.pipeline.to_papermage(doc)
    
    def from_pdf(self, pdf_path: Union[str, Path]) -> Any:
        """
        Process a PDF file using the recipe.
        
        This method matches PaperMage's CoreRecipe.from_pdf() method.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Processed document in PaperMage-compatible format
        """
        return self.run(str(pdf_path))
    
    @classmethod
    def default(cls) -> "CoreRecipe":
        """
        Create a CoreRecipe with default settings.
        
        Returns:
            Configured CoreRecipe instance
        """
        return cls() 