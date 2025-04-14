"""
Predictors module for document structure and language prediction.

This module provides utilities for predicting document structure, 
language detection, and RTL text processing.
"""

# Export RTL utilities
from papermage_docling.predictors.rtl_utils import (
    is_rtl,
    is_rtl_char,
    get_text_direction,
    reorder_text,
    reorder_words,
    process_rtl_paragraph,
    process_mixed_text,
    normalize_rtl_text,
    detect_and_mark_rtl,
)

# Export language prediction
from papermage_docling.predictors.language_predictor import (
    LanguagePredictor,
    is_rtl_language,
    get_language_name,
    detect_language,
    get_language_predictor,
)

# Export structure prediction
from papermage_docling.predictors.structure_predictor import (
    StructurePredictor,
    get_structure_predictor,
)

# Export figure prediction
from papermage_docling.predictors.figure_predictor import (
    FigurePredictor,
    FigureItem,
    get_figure_predictor,
)

# Export table prediction
from papermage_docling.predictors.table_predictor import (
    TablePredictor,
    TableItem,
    get_table_predictor,
)

__all__ = [
    # RTL utilities
    'is_rtl',
    'is_rtl_char',
    'get_text_direction',
    'reorder_text',
    'reorder_words',
    'process_rtl_paragraph',
    'process_mixed_text',
    'normalize_rtl_text',
    'detect_and_mark_rtl',
    
    # Language prediction
    'LanguagePredictor',
    'is_rtl_language',
    'get_language_name',
    'detect_language',
    'get_language_predictor',
    
    # Structure prediction
    'StructurePredictor',
    'get_structure_predictor',
    
    # Figure prediction
    'FigurePredictor',
    'FigureItem',
    'get_figure_predictor',
    
    # Table prediction
    'TablePredictor',
    'TableItem',
    'get_table_predictor',
]
