"""
Pipeline service for managing document processing pipelines.

This service provides methods for configuring and managing the document
processing pipeline, including predictor configuration and pipeline customization.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Type

from app.core.config import settings
from app.services.base import BaseService

# Import papermage_docling components
try:
    from papermage_docling.pipeline import Pipeline, SimplePipeline, DocumentProcessor
    from papermage_docling.predictors import (
        StructurePredictor, FigurePredictor, TablePredictor, LanguagePredictor,
        get_language_predictor, get_structure_predictor, get_figure_predictor, get_table_predictor
    )
    DOCLING_AVAILABLE = True
except ImportError:
    logging.warning("papermage_docling not available. Pipeline service will be disabled.")
    DOCLING_AVAILABLE = False

logger = logging.getLogger(__name__)


class PipelineService(BaseService):
    """
    Service for managing document processing pipelines.
    
    This service provides methods for configuring and customizing the
    document processing pipeline, including predictor configuration.
    """
    
    def __init__(self):
        """Initialize the pipeline service."""
        super().__init__()
        
        if not DOCLING_AVAILABLE:
            logger.warning("Pipeline service initialized without docling support.")
            return
            
        try:
            from papermage_docling.api_service import get_api_service
            self.api_service = get_api_service()
            self.pipeline = self.api_service.pipeline
            
            # Store predictor instances
            self.predictors = {}
            self._initialize_predictors()
            
            logger.info("Initialized pipeline service with docling support.")
        except Exception as e:
            logger.error(f"Failed to initialize pipeline service: {e}")
            raise
    
    def _initialize_predictors(self):
        """Initialize the predictor instances."""
        if not DOCLING_AVAILABLE:
            return
            
        try:
            # Structure predictor
            self.predictors['structure'] = get_structure_predictor()
            
            # Figure predictor
            self.predictors['figure'] = get_figure_predictor()
            
            # Table predictor
            self.predictors['table'] = get_table_predictor()
            
            # Language predictor
            self.predictors['language'] = get_language_predictor()
            
            logger.info("Initialized predictors.")
        except Exception as e:
            logger.error(f"Failed to initialize predictors: {e}")
            raise
    
    def get_pipeline_config(self) -> Dict[str, Any]:
        """
        Get the current pipeline configuration.
        
        Returns:
            Dictionary with pipeline configuration
        """
        if not DOCLING_AVAILABLE:
            raise ValueError("Pipeline service is not available (docling not installed)")
        
        pipeline = self.pipeline
        
        # Extract pipeline type
        pipeline_type = "SimplePipeline" if isinstance(pipeline, SimplePipeline) else "Pipeline"
        
        # Extract steps
        steps = [step.__class__.__name__ for step in pipeline.steps]
        
        # Extract configuration
        config = {
            "ocr_enabled": getattr(pipeline, "ocr_enabled", settings.OCR_ENABLED),
            "ocr_language": getattr(pipeline, "ocr_language", settings.OCR_LANGUAGE),
            "detect_rtl": getattr(pipeline, "detect_rtl", settings.DETECT_RTL),
        }
        
        # Add predictor-specific configurations
        predictor_configs = {}
        for predictor_name, predictor in self.predictors.items():
            if hasattr(predictor, 'get_config'):
                predictor_configs[predictor_name] = predictor.get_config()
            else:
                # Extract basic attributes if get_config not available
                predictor_configs[predictor_name] = {
                    k: getattr(predictor, k) 
                    for k in dir(predictor) 
                    if not k.startswith('_') and not callable(getattr(predictor, k))
                }
        
        return {
            "pipeline_type": pipeline_type,
            "steps": steps,
            "config": config,
            "predictors": predictor_configs
        }
    
    def configure_predictor(self, predictor_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure a specific predictor.
        
        Args:
            predictor_type: The type of predictor (structure, figure, table, language)
            config: Configuration parameters
            
        Returns:
            Updated predictor configuration
        """
        if not DOCLING_AVAILABLE:
            raise ValueError("Pipeline service is not available (docling not installed)")
        
        if predictor_type not in self.predictors:
            raise ValueError(f"Predictor type '{predictor_type}' not found")
        
        predictor = self.predictors[predictor_type]
        
        # Update predictor configuration
        for key, value in config.items():
            if hasattr(predictor, key):
                setattr(predictor, key, value)
        
        # Get updated configuration
        updated_config = {}
        if hasattr(predictor, 'get_config'):
            updated_config = predictor.get_config()
        else:
            updated_config = {
                k: getattr(predictor, k) 
                for k in dir(predictor) 
                if not k.startswith('_') and not callable(getattr(predictor, k))
            }
        
        return updated_config
    
    def customize_pipeline(self, steps: List[str], parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Customize the document processing pipeline.
        
        Args:
            steps: Ordered list of pipeline step names to enable
            parameters: Pipeline-wide parameters
            
        Returns:
            Updated pipeline configuration
        """
        if not DOCLING_AVAILABLE:
            raise ValueError("Pipeline service is not available (docling not installed)")
        
        if parameters is None:
            parameters = {}
        
        # Create a new pipeline
        pipeline = SimplePipeline(name="CustomPipeline")
        
        # Configure pipeline parameters
        for key, value in parameters.items():
            if hasattr(pipeline, key):
                setattr(pipeline, key, value)
        
        # Create processor class for predictor wrapping
        class PredictorProcessor(DocumentProcessor):
            def __init__(self, name, predictor):
                super().__init__(name)
                self.predictor = predictor
            
            def process(self, doc, **kwargs):
                # Use the predict_docling method if available, otherwise fall back
                if hasattr(self.predictor, 'predict_docling'):
                    return self.predictor.predict_docling(doc, **kwargs)
                else:
                    # Fallback
                    logger.warning(f"Predictor {self.name} doesn't implement predict_docling")
                    return doc
        
        # Add requested steps
        for step_name in steps:
            if step_name.lower() == 'language':
                pipeline.add_processor(
                    PredictorProcessor("LanguageDetection", self.predictors['language'])
                )
            elif step_name.lower() == 'structure':
                pipeline.add_processor(
                    PredictorProcessor("StructureAnalysis", self.predictors['structure'])
                )
            elif step_name.lower() == 'table':
                pipeline.add_processor(
                    PredictorProcessor("TableDetection", self.predictors['table'])
                )
            elif step_name.lower() == 'figure':
                pipeline.add_processor(
                    PredictorProcessor("FigureDetection", self.predictors['figure'])
                )
            else:
                logger.warning(f"Unknown step name: {step_name}")
        
        # Set the customized pipeline
        self.api_service.pipeline = pipeline
        self.pipeline = pipeline
        
        return self.get_pipeline_config()
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Get pipeline statistics.
        
        Returns:
            Dictionary with pipeline statistics
        """
        if not DOCLING_AVAILABLE:
            raise ValueError("Pipeline service is not available (docling not installed)")
        
        return self.api_service.get_pipeline_stats()
    
    def analyze_document(self, document_id: str, analysis_type: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform document analysis.
        
        Args:
            document_id: The document ID
            analysis_type: Type of analysis to perform
            parameters: Analysis parameters
            
        Returns:
            Analysis results
        """
        if not DOCLING_AVAILABLE:
            raise ValueError("Pipeline service is not available (docling not installed)")
        
        if parameters is None:
            parameters = {}
        
        # Get the document
        doc = self.api_service.get_document(document_id)
        
        # Perform analysis based on type
        if analysis_type == 'language':
            return self._analyze_language(doc, parameters)
        elif analysis_type == 'structure':
            return self._analyze_structure(doc, parameters)
        elif analysis_type == 'tables':
            return self._analyze_tables(doc, parameters)
        elif analysis_type == 'figures':
            return self._analyze_figures(doc, parameters)
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
    
    def _analyze_language(self, doc, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform language analysis."""
        predictor = self.predictors['language']
        
        # Extract text from document
        text = doc.get_full_text() if hasattr(doc, 'get_full_text') else ""
        
        # Analyze language
        results = predictor.predict_document_language(text)
        
        return {
            "document_language": results.get('language'),
            "language_name": results.get('language_name'),
            "confidence": results.get('confidence'),
            "is_rtl": results.get('is_rtl'),
            "additional_languages": results.get('additional_languages', [])
        }
    
    def _analyze_structure(self, doc, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform structure analysis."""
        predictor = self.predictors['structure']
        
        # Analysis logic depends on the specific predictor implementation
        # This is a simplified version
        return {
            "sections_count": len(getattr(doc, 'sections', [])),
            "paragraphs_count": len(getattr(doc, 'paragraphs', [])),
            "structure_hierarchy": "Document structure analysis result"
        }
    
    def _analyze_tables(self, doc, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform table analysis."""
        predictor = self.predictors['table']
        
        # Analysis logic depends on the specific predictor implementation
        return {
            "tables_count": len(getattr(doc, 'tables', [])),
            "tables_by_page": "Table breakdown by page"
        }
    
    def _analyze_figures(self, doc, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform figure analysis."""
        predictor = self.predictors['figure']
        
        # Analysis logic depends on the specific predictor implementation
        return {
            "figures_count": len(getattr(doc, 'figures', [])),
            "figures_by_page": "Figure breakdown by page"
        } 