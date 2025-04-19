"""
DEPRECATED Predictors module for document structure and language prediction.

This module provides compatibility stubs for the predictor functionality.
Docling now handles these features internally through its DocumentConverter API.

This module will be removed in a future version.
"""

import importlib.util
import logging
import warnings
from typing import Any, Dict, List, Optional, Union

from .base import BasePredictor
from .figure import FigurePredictor
from .language import LanguagePredictor
from .layout import LayoutPredictor
from .structure import StructurePredictor
from .table import TablePredictor

try:
    from papermage_docling.converter import convert_document
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

logger = logging.getLogger(__name__)

# Display a module-level deprecation warning
warnings.warn(
    "The papermage_docling.predictors module is deprecated and will be removed in a future version. "
    "Use Docling's native functionality via DocumentConverter instead.",
    DeprecationWarning,
    stacklevel=2
)

# Base predictor class for compatibility
class BasePredictor:
    """
    Legacy compatibility class for base predictor.
    
    DEPRECATED: This class is maintained only for backward compatibility.
    Docling now handles these features internally.
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
    name = "figures"
    description = "Detects figures in documents using Docling."

    def analyze(self, document_path: str, **kwargs) -> Any:
        if not DOCLING_AVAILABLE:
            raise RuntimeError("Docling not available for figure analysis.")
        result = convert_document(document_path, options={"figures": True})
        return result.get("figures", {})

# For compatibility with code that imports TablePredictor
class TablePredictor(BasePredictor):
    """
    Legacy compatibility class for table prediction.
    
    DEPRECATED: This class is maintained only for backward compatibility.
    Docling now handles table detection internally.
    """
    name = "tables"
    description = "Detects tables in documents using Docling."

    def analyze(self, document_path: str, include_data: bool = False, **kwargs) -> Any:
        if not DOCLING_AVAILABLE:
            raise RuntimeError("Docling not available for table analysis.")
        result = convert_document(document_path, options={"tables": True, "include_data": include_data})
        return result.get("tables", {})

# For compatibility with code that imports LanguagePredictor
class LanguagePredictor(BasePredictor):
    """
    Legacy compatibility class for language prediction.
    
    DEPRECATED: This class is maintained only for backward compatibility.
    Docling now handles language detection internally.
    """
    name = "language"
    description = "Predicts document language using Docling."

    def analyze(self, document_path: str, min_confidence: float = 0.2, **kwargs) -> Any:
        if not DOCLING_AVAILABLE:
            raise RuntimeError("Docling not available for language analysis.")
        result = convert_document(document_path, options={"language": True, "min_confidence": min_confidence})
        # Extract language info from result (customize as needed)
        return result.get("language", {})

# For compatibility with code that imports StructurePredictor
class StructurePredictor(BasePredictor):
    """
    Legacy compatibility class for structure prediction.
    
    DEPRECATED: This class is maintained only for backward compatibility.
    Docling now handles document structure analysis internally.
    """
    name = "structure"
    description = "Analyzes document structure (sections, paragraphs, etc.) using Docling."

    def analyze(self, document_path: str, detailed: bool = False, **kwargs) -> Any:
        if not DOCLING_AVAILABLE:
            raise RuntimeError("Docling not available for structure analysis.")
        result = convert_document(document_path, options={"structure": True, "detailed": detailed})
        return result.get("structure", {})

# For compatibility with code that imports the factories
def get_figure_predictor(*args, **kwargs):
    """Get a figure predictor instance. Deprecated stub."""
    warnings.warn(
        "get_figure_predictor is deprecated. Docling now handles figure detection internally.",
        DeprecationWarning,
        stacklevel=2
    )
    return FigurePredictor()

def get_table_predictor(*args, **kwargs):
    """Get a table predictor instance. Deprecated stub."""
    warnings.warn(
        "get_table_predictor is deprecated. Docling now handles table detection internally.",
        DeprecationWarning,
        stacklevel=2
    )
    return TablePredictor()

def get_structure_predictor(*args, **kwargs):
    """Get a structure predictor instance. Deprecated stub."""
    warnings.warn(
        "get_structure_predictor is deprecated. Docling now handles structure detection internally.",
        DeprecationWarning,
        stacklevel=2
    )
    return StructurePredictor()

def get_language_predictor(*args, **kwargs):
    """Get a language predictor instance. Deprecated stub."""
    warnings.warn(
        "get_language_predictor is deprecated. Docling now handles language detection internally.",
        DeprecationWarning,
        stacklevel=2
    )
    return LanguagePredictor()

# RTL utility functions (these are now directly using Docling's capabilities when available)
def is_rtl(text: str) -> bool:
    """
    Check if text is primarily right-to-left.
    
    Args:
        text: The text to check
        
    Returns:
        True if text is primarily RTL, False otherwise
    """
    # Use docling's RTL detection if available
    if DOCLING_AVAILABLE:
        try:
            from docling.utils.rtl import is_rtl_text
            return is_rtl_text(text)
        except ImportError:
            pass
    
    # Fallback RTL detection for backward compatibility
    if not text:
        return False
    
    rtl_chars = 0
    for char in text:
        if is_rtl_char(char):
            rtl_chars += 1
    
    return rtl_chars > len(text) / 2

def is_rtl_char(char: str) -> bool:
    """
    Check if a character is from an RTL script.
    
    Args:
        char: A single character to check
        
    Returns:
        True if the character is from an RTL script, False otherwise
    """
    # Hebrew: 0x0590-0x05FF
    # Arabic: 0x0600-0x06FF
    # Extended Arabic: 0x0750-0x077F
    # Various Arabic presentations: 0xFB50-0xFDFF, 0xFE70-0xFEFF
    code = ord(char)
    return (
        (0x0590 <= code <= 0x05FF) or  # Hebrew
        (0x0600 <= code <= 0x06FF) or  # Arabic
        (0x0750 <= code <= 0x077F) or  # Extended Arabic
        (0xFB50 <= code <= 0xFDFF) or  # Arabic presentation forms A
        (0xFE70 <= code <= 0xFEFF)      # Arabic presentation forms B
    )

def get_text_direction(text: str) -> str:
    """
    Get the primary text direction.
    
    Args:
        text: The text to analyze
        
    Returns:
        'rtl' if the text is primarily right-to-left, 'ltr' otherwise
    """
    return "rtl" if is_rtl(text) else "ltr"

def reorder_text(text: str) -> str:
    """
    Reorder RTL text for proper display.
    
    Args:
        text: The text to reorder
        
    Returns:
        Reordered text
    """
    warnings.warn(
        "reorder_text is deprecated. Docling now handles RTL text internally.",
        DeprecationWarning,
        stacklevel=2
    )
    return text

def reorder_words(words: List[str]) -> List[str]:
    """
    Reorder a list of words for RTL text.
    
    Args:
        words: List of words to reorder
        
    Returns:
        Reordered list of words
    """
    warnings.warn(
        "reorder_words is deprecated. Docling now handles RTL text internally.",
        DeprecationWarning,
        stacklevel=2
    )
    return words

def process_rtl_paragraph(text: str) -> str:
    """
    Process an RTL paragraph for proper display.
    
    Args:
        text: The RTL paragraph text
        
    Returns:
        Processed text
    """
    warnings.warn(
        "process_rtl_paragraph is deprecated. Docling now handles RTL text internally.",
        DeprecationWarning,
        stacklevel=2
    )
    return text

def process_mixed_text(text: str) -> str:
    """
    Process text with mixed RTL and LTR content.
    
    Args:
        text: The mixed text
        
    Returns:
        Processed text
    """
    warnings.warn(
        "process_mixed_text is deprecated. Docling now handles mixed RTL/LTR text internally.",
        DeprecationWarning,
        stacklevel=2
    )
    return text

def normalize_rtl_text(text: str) -> str:
    """
    Normalize RTL text (e.g., handle ligatures, normalize characters).
    
    Args:
        text: The RTL text to normalize
        
    Returns:
        Normalized text
    """
    warnings.warn(
        "normalize_rtl_text is deprecated. Docling now handles RTL text normalization internally.",
        DeprecationWarning,
        stacklevel=2
    )
    return text

def detect_and_mark_rtl(document: Any) -> Any:
    """
    Detect and mark RTL sections in a document.
    
    Args:
        document: The document to process
        
    Returns:
        Processed document
    """
    warnings.warn(
        "detect_and_mark_rtl is deprecated. Docling now handles RTL detection internally.",
        DeprecationWarning,
        stacklevel=2
    )
    return document

# For compatibility with code that imports these from predictors
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

def get_language_name(language_code: str) -> str:
    """
    Get the name of a language from its code.
    
    Args:
        language_code: ISO language code
        
    Returns:
        Language name
    """
    language_names = {
        'en': 'English',
        'fr': 'French',
        'de': 'German',
        'es': 'Spanish',
        'it': 'Italian',
        'pt': 'Portuguese',
        'nl': 'Dutch',
        'ru': 'Russian',
        'ar': 'Arabic',
        'he': 'Hebrew',
        'fa': 'Persian',
        'zh': 'Chinese',
        'ja': 'Japanese',
        'ko': 'Korean',
    }
    return language_names.get(language_code.lower(), f"Unknown ({language_code})")

def detect_language(text: str) -> str:
    """
    Detect the language of text.
    
    Args:
        text: The text to analyze
        
    Returns:
        ISO language code
    """
    warnings.warn(
        "detect_language is deprecated. Use Docling's native language detection via DocumentConverter.",
        DeprecationWarning,
        stacklevel=2
    )
    # Default to English for backward compatibility
    return "en"

# Export names for backward compatibility
__all__ = [
    "BasePredictor",
    "LanguagePredictor",
    "StructurePredictor",
    "TablePredictor",
    "FigurePredictor",
    "LayoutPredictor",
]

# Compatibility items
class FigureItem:
    """Compatibility stub for FigureItem."""
    pass

class TableItem:
    """Compatibility stub for TableItem."""
    pass

class LayoutPredictor(BasePredictor):
    name = "layout"
    description = "Analyzes document layout using Docling."

    def analyze(self, document_path: str, **kwargs) -> Any:
        if not DOCLING_AVAILABLE:
            raise RuntimeError("Docling not available for layout analysis.")
        result = convert_document(document_path, options={"layout": True})
        return result.get("layout", {})

# Plugin extension example:
# class MyCustomPredictor(BasePredictor):
#     name = "my_custom"
#     description = "My custom analysis predictor."
#     def analyze(self, document_path: str, **kwargs):
#         # Custom logic
#         return {}
