"""
Analysis service for document analysis features (figures, tables, layout, tables, structure, language, etc.).

This service wraps Docling predictors and models, providing a clean, extensible interface for the API layer.
Supports advanced pipeline options (do_code_enrichment, do_formula_enrichment, do_picture_classification, do_table_structure, etc.).
"""

import logging
from typing import Any, Dict

try:
    from papermage_docling.predictors import (
        FigurePredictor,
        LanguagePredictor,
        LayoutPredictor,
        StructurePredictor,
        TablePredictor,
    )
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

logger = logging.getLogger(__name__)

class AnalysisService:
    """
    Service for document analysis using Docling predictors.
    Exposes high-level analysis methods and supports advanced pipeline options.
    """
    def __init__(self):
        if not DOCLING_AVAILABLE:
            logger.warning("Docling predictors not available. Analysis features will be disabled.")
            self.figure_predictor = None
            self.table_predictor = None
            self.layout_predictor = None
            self.structure_predictor = None
            self.language_predictor = None
        else:
            self.figure_predictor = FigurePredictor()
            self.table_predictor = TablePredictor()
            self.layout_predictor = LayoutPredictor()
            self.structure_predictor = StructurePredictor()
            self.language_predictor = LanguagePredictor()

    def analyze_figures(self, document_path: str, **kwargs) -> Dict[str, Any]:
        """
        Analyze figures in a document. Accepts advanced pipeline options as kwargs.
        """
        if not self.figure_predictor:
            raise RuntimeError("Figure analysis is not available (docling not installed)")
        return self.figure_predictor.analyze(document_path, **kwargs)

    def analyze_tables(self, document_path: str, **kwargs) -> Dict[str, Any]:
        """
        Analyze tables in a document. Accepts advanced pipeline options as kwargs.
        """
        if not self.table_predictor:
            raise RuntimeError("Table analysis is not available (docling not installed)")
        return self.table_predictor.analyze(document_path, **kwargs)

    def analyze_layout(self, document_path: str, **kwargs) -> Dict[str, Any]:
        """
        Analyze layout in a document. Accepts advanced pipeline options as kwargs.
        """
        if not self.layout_predictor:
            raise RuntimeError("Layout analysis is not available (docling not installed)")
        return self.layout_predictor.analyze(document_path, **kwargs)

    def analyze_structure(self, document_path: str, **kwargs) -> Dict[str, Any]:
        """
        Analyze document structure (sections, paragraphs, etc.). Accepts advanced pipeline options as kwargs.
        """
        if not self.structure_predictor:
            raise RuntimeError("Structure analysis is not available (docling not installed)")
        return self.structure_predictor.analyze(document_path, **kwargs)

    def analyze_language(self, document_path: str, **kwargs) -> Dict[str, Any]:
        """
        Analyze document language using langdetect. Accepts min_confidence and other kwargs.
        """
        if not self.language_predictor:
            raise RuntimeError("Language analysis is not available (langdetect not installed)")
        return self.language_predictor.analyze(document_path, **kwargs) 