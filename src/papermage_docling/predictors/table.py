"""
Table predictor for table detection in documents using Docling.
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

class TablePredictor(BasePredictor):
    name = "tables"
    description = "Detects tables in documents using Docling. Supports advanced pipeline options."

    def analyze(self, document_path: str, include_data: bool = False, **kwargs):
        """
        Analyze tables in a document.
        Args:
            document_path: Path to the document file
            include_data: Whether to include table data
            kwargs: Advanced pipeline options (do_code_enrichment, do_formula_enrichment, do_picture_classification, do_table_structure, etc.)
        Returns:
            Table analysis result
        """
        if not DOCLING_AVAILABLE:
            raise RuntimeError("Docling not available for table analysis.")
        options = {"tables": True, "include_data": include_data}
        options.update(kwargs)
        result = convert_document(document_path, options=options)
        return result.get("entities", {}).get("tables", {}) 