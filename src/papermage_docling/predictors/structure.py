"""
Structure predictor for document structure analysis using Docling.
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

class StructurePredictor(BasePredictor):
    name = "structure"
    description = "Analyzes document structure (sections, paragraphs, etc.) using Docling. Supports advanced pipeline options."

    def analyze(self, document_path: str, detailed: bool = False, **kwargs):
        """
        Analyze document structure.
        Args:
            document_path: Path to the document file
            detailed: Whether to include detailed structure analysis
            kwargs: Advanced pipeline options (do_code_enrichment, do_formula_enrichment, do_picture_classification, do_table_structure, etc.)
        Returns:
            Structure analysis result
        """
        if not DOCLING_AVAILABLE:
            raise RuntimeError("Docling not available for structure analysis.")
        options = {"structure": True, "detailed": detailed}
        options.update(kwargs)
        result = convert_document(document_path, options=options)
        return result.get("structure", {}) 