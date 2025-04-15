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

"""
Legacy predictors compatibility layer.

This module provides stubs and compatibility imports for code that might
still reference the old predictor classes, which have been removed in favor
of direct Docling integration.

DEPRECATED: These are placeholder compatibility classes that will be removed in a future version.
"""

import warnings
from typing import Any, Dict, List, Optional

# Base predictor class for compatibility
class BasePredictor:
    """
    Legacy compatibility class for base predictor.
    
    DEPRECATED: This class is maintained only for backward compatibility.
    """
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "BasePredictor is deprecated and will be removed in a future version. "
            "Docling now handles these features internally.",
            DeprecationWarning,
            stacklevel=2
        )
    
    def process(self, *args, **kwargs):
        """Stub method for compatibility."""
        warnings.warn(
            "BasePredictor.process is deprecated and will be removed in a future version. "
            "Docling now handles these features internally.",
            DeprecationWarning,
            stacklevel=2
        )
        return args[0] if args else None

# For compatibility with code that imports FigurePredictor
class FigurePredictor(BasePredictor):
    """
    Legacy compatibility class for figure prediction.
    
    DEPRECATED: This class is maintained only for backward compatibility.
    Docling now handles figure detection internally.
    """
    pass

# For compatibility with code that imports TablePredictor
class TablePredictor(BasePredictor):
    """
    Legacy compatibility class for table prediction.
    
    DEPRECATED: This class is maintained only for backward compatibility.
    Docling now handles table detection internally.
    """
    pass

# For compatibility with code that imports LanguagePredictor
class LanguagePredictor(BasePredictor):
    """
    Legacy compatibility class for language prediction.
    
    DEPRECATED: This class is maintained only for backward compatibility.
    Docling now handles language detection internally.
    """
    pass

# For compatibility with code that imports StructurePredictor
class StructurePredictor(BasePredictor):
    """
    Legacy compatibility class for structure prediction.
    
    DEPRECATED: This class is maintained only for backward compatibility.
    Docling now handles document structure analysis internally.
    """
    pass

# RTL utils compatibility functions
def is_rtl_language(language_code: str) -> bool:
    """
    Check if a language is right-to-left.
    
    Args:
        language_code: ISO language code
        
    Returns:
        True if the language is RTL, False otherwise
    """
    rtl_languages = {'ar', 'he', 'fa', 'ur', 'dv', 'ha', 'khw', 'ks', 'ku', 'ps', 'sd', 'ug', 'yi'}
    return language_code.lower() in rtl_languages
