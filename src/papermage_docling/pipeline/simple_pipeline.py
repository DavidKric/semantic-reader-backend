"""
Simple document processing pipeline implementation.

This module provides a simplified pipeline implementation
for common document processing tasks.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Callable

from papermage_docling.pipeline.pipeline import Pipeline, DocumentProcessor

# Import the DoclingDocument from docling_core
try:
    from docling_core.types import DoclingDocument
except ImportError:
    logging.warning("docling_core not found. Document pipeline will not be available.")
    # Define a stub class for type hints only
    class DoclingDocument:
        pass

# Import adapters for format conversion
from papermage_docling.adapters import PaperMageAdapter

logger = logging.getLogger(__name__)


class SimplePipeline(Pipeline):
    """
    A simplified document processing pipeline using DoclingDocument.
    
    This class provides a higher-level interface for building document
    processing pipelines with common processing steps and convenient
    methods for common operations.
    """
    
    def __init__(self, name: str = "SimplePipeline"):
        """
        Initialize a simple document processing pipeline.
        
        Args:
            name: Name of the pipeline for identification and logging
        """
        super().__init__(name=name)
        logger.info(f"Initialized SimplePipeline: {name}")
    
    def add_processor(
        self,
        processor: DocumentProcessor,
        **kwargs
    ) -> "SimplePipeline":
        """
        Add a document processor to the pipeline with default settings.
        
        Args:
            processor: The document processor to add
            **kwargs: Additional options to pass to add_step
            
        Returns:
            The pipeline instance for method chaining
        """
        self.add_step(processor, **kwargs)
        return self
    
    def from_papermage(self, pm_doc: Any) -> DoclingDocument:
        """
        Convert a PaperMage document to DoclingDocument.
        
        This method is used at API boundaries to convert from external
        formats to the internal DoclingDocument format.
        
        Args:
            pm_doc: PaperMage document to convert
            
        Returns:
            Converted DoclingDocument
        """
        logger.info("Converting PaperMage document to DoclingDocument at API boundary")
        return PaperMageAdapter.from_papermage(pm_doc)
    
    def to_papermage(self, doc: DoclingDocument) -> Any:
        """
        Convert a DoclingDocument to PaperMage format.
        
        This method is used at API boundaries to convert from internal
        DoclingDocument format to external formats.
        
        Args:
            doc: DoclingDocument to convert
            
        Returns:
            Converted PaperMage document
        """
        logger.info("Converting DoclingDocument to PaperMage format at API boundary")
        return PaperMageAdapter.to_papermage(doc)
    
    def process_file(self, file_path: str, **kwargs) -> DoclingDocument:
        """
        Process a document file through the pipeline.
        
        Args:
            file_path: Path to the document file
            **kwargs: Additional processing options
            
        Returns:
            The processed DoclingDocument
        """
        logger.info(f"Processing file: {file_path}")
        
        # Import document parsing functionality
        from docling_parse.pdf_parser import parse_pdf
        
        # Parse the PDF to DoclingDocument directly
        doc = parse_pdf(file_path)
        
        # Process through the pipeline
        return self.process(doc, **kwargs)
    
    @classmethod
    def create_default_pipeline(cls) -> "SimplePipeline":
        """
        Create a default pipeline with common processing steps.
        
        Returns:
            Configured SimplePipeline instance
        """
        pipeline = cls(name="DefaultPipeline")
        
        # Import predictors
        from papermage_docling.predictors import (
            get_table_predictor, get_figure_predictor, 
            get_structure_predictor, get_language_predictor
        )
        
        # Create processors wrapping the predictors
        class PredictorProcessor(DocumentProcessor):
            def __init__(self, name, predictor):
                super().__init__(name)
                self.predictor = predictor
            
            def process(self, doc, **kwargs):
                # Use the predict_docling method if available, otherwise fall back
                if hasattr(self.predictor, 'predict_docling'):
                    return self.predictor.predict_docling(doc, **kwargs)
                else:
                    # This is a fallback and generally shouldn't be used in the refactored system
                    logger.warning(f"Predictor {self.name} doesn't implement predict_docling, using legacy method")
                    prediction_result = self.predictor.predict(doc, **kwargs)
                    
                    # Here we would need to convert the result back to DoclingDocument
                    # This code path should be eliminated as predictors are updated
                    return doc
        
        # Add common processing steps
        pipeline.add_processor(
            PredictorProcessor("LanguageDetection", get_language_predictor())
        )
        
        pipeline.add_processor(
            PredictorProcessor("StructureAnalysis", get_structure_predictor())
        )
        
        pipeline.add_processor(
            PredictorProcessor("TableDetection", get_table_predictor())
        )
        
        pipeline.add_processor(
            PredictorProcessor("FigureDetection", get_figure_predictor())
        )
        
        logger.info("Created default pipeline with common processing steps")
        return pipeline 