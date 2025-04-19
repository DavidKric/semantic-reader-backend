"""
Figure predictor for figure detection in documents using Docling.
Supports advanced pipeline options: do_code_enrichment, do_formula_enrichment, do_picture_classification, do_table_structure, etc.
"""
import logging

from .base import BasePredictor

try:
    from papermage_docling.converter import convert_document
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

logger = logging.getLogger(__name__)

class FigurePredictor(BasePredictor):
    name = "figures"
    description = "Detects figures in documents using Docling. Supports advanced pipeline options."

    def analyze(self, document_path: str, **kwargs):
        """
        Analyze figures in a document.
        Args:
            document_path: Path to the document file
            kwargs: Advanced pipeline options (do_code_enrichment, do_formula_enrichment, do_picture_classification, do_table_structure, etc.)
        Returns:
            Figure analysis result
        """
        if not DOCLING_AVAILABLE:
            raise RuntimeError("Docling not available for figure analysis.")
        options = {"figures": True}
        options.update(kwargs)
        result = convert_document(document_path, options=options)
        return result.get("entities", {}).get("figures", {}) 