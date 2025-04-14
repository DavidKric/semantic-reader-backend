"""
Utilities for handling right-to-left (RTL) text in document processing.

This module provides functions for detecting and processing RTL text in documents,
which is essential for proper rendering of languages like Arabic, Hebrew, and Persian.
"""

import re
import unicodedata
from typing import List, Tuple, Optional
import logging

# Import bidi processing libraries for RTL handling
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_BIDI_SUPPORT = True
except ImportError:
    HAS_BIDI_SUPPORT = False
    logging.warning(
        "arabic-reshaper and python-bidi libraries not found. "
        "RTL text processing will be limited. "
        "Install with: pip install arabic-reshaper python-bidi"
    )

logger = logging.getLogger(__name__)

# RTL language codes (ISO 639-1)
RTL_LANGUAGE_CODES = {
    "ar": "Arabic",
    "arc": "Aramaic",
    "dv": "Dhivehi",
    "fa": "Persian",
    "ha": "Hausa",
    "he": "Hebrew",
    "khw": "Khowar",
    "ks": "Kashmiri",
    "ku": "Kurdish",
    "ps": "Pashto",
    "ur": "Urdu",
    "yi": "Yiddish"
}

# Unicode ranges for RTL scripts
RTL_UNICODE_RANGES = [
    (0x0590, 0x05FF),    # Hebrew
    (0x0600, 0x06FF),    # Arabic
    (0x0700, 0x074F),    # Syriac
    (0x0750, 0x077F),    # Arabic Supplement
    (0x08A0, 0x08FF),    # Arabic Extended-A
    (0xFB50, 0xFDFF),    # Arabic Presentation Forms-A
    (0xFE70, 0xFEFF),    # Arabic Presentation Forms-B
    (0x10800, 0x10FFF),  # Other RTL scripts
]

def is_rtl_language(language_code: str) -> bool:
    """
    Check if a language code corresponds to a right-to-left language.
    
    Args:
        language_code: ISO 639-1 or 639-3 language code
        
    Returns:
        True if the language is RTL, False otherwise
    """
    return language_code.lower() in RTL_LANGUAGE_CODES

def contains_rtl_characters(text: str) -> bool:
    """
    Check if a string contains right-to-left characters.
    
    Args:
        text: The string to check
        
    Returns:
        True if RTL characters are found, False otherwise
    """
    if not text:
        return False
    
    for char in text:
        char_code = ord(char)
        for start, end in RTL_UNICODE_RANGES:
            if start <= char_code <= end:
                return True
    return False

def estimate_rtl_ratio(text: str) -> float:
    """
    Estimate the ratio of RTL characters in a text.
    
    Args:
        text: The text to analyze
        
    Returns:
        Ratio (0.0 to 1.0) of RTL characters to total text length
    """
    if not text:
        return 0.0
    
    rtl_count = 0
    for char in text:
        char_code = ord(char)
        for start, end in RTL_UNICODE_RANGES:
            if start <= char_code <= end:
                rtl_count += 1
                break
    
    return rtl_count / len(text)

def detect_rtl_text(text: str, threshold: float = 0.3) -> bool:
    """
    Detect if a text should be treated as right-to-left.
    
    Args:
        text: The text to analyze
        threshold: Minimum ratio of RTL characters to consider the text as RTL
        
    Returns:
        True if the text should be treated as RTL, False otherwise
        
    Raises:
        TypeError: If text is None
    """
    if text is None:
        raise TypeError("Text cannot be None")
    return estimate_rtl_ratio(text) >= threshold

def get_rtl_direction_marker(is_rtl: bool) -> str:
    """
    Get the appropriate Unicode bidirectional marker.
    
    Args:
        is_rtl: Whether the text is RTL
        
    Returns:
        Unicode RLM (Right-to-Left Mark) or LRM (Left-to-Right Mark)
    """
    # Unicode bidi control characters
    RLM = "\u200F"  # Right-to-Left Mark
    LRM = "\u200E"  # Left-to-Right Mark
    
    return RLM if is_rtl else LRM

def apply_rtl_processing(text: str) -> str:
    """
    Apply RTL processing to text when needed.
    
    This function analyzes the text and adds appropriate bidirectional markers
    to ensure correct rendering of mixed LTR/RTL content.
    
    Args:
        text: The text to process
        
    Returns:
        Processed text with appropriate bidirectional markers
    """
    if not text:
        return text
    
    is_rtl = detect_rtl_text(text)
    bidi_marker = get_rtl_direction_marker(is_rtl)
    
    # Add bidirectional isolation markers for mixed content
    RLI = "\u2067"  # Right-to-Left Isolate
    LRI = "\u2066"  # Left-to-Right Isolate
    PDI = "\u2069"  # Pop Directional Isolate
    
    # Simple processing: apply isolation if RTL is detected
    if is_rtl:
        return f"{RLI}{text}{PDI}"
    
    return text

def segment_rtl_sections(text: str) -> List[Tuple[str, bool]]:
    """
    Segment text into RTL and non-RTL sections.
    
    Args:
        text: The text to segment
        
    Returns:
        List of tuples containing (text_segment, is_rtl)
    """
    if not text:
        return []
    
    # Simple implementation - in production, this would use a more sophisticated
    # algorithm to properly segment mixed text
    segments = []
    current_segment = ""
    current_is_rtl = None
    
    for char in text:
        char_is_rtl = False
        char_code = ord(char)
        
        for start, end in RTL_UNICODE_RANGES:
            if start <= char_code <= end:
                char_is_rtl = True
                break
        
        # Start a new segment if direction changes
        if current_is_rtl is None:
            current_is_rtl = char_is_rtl
            current_segment += char
        elif current_is_rtl != char_is_rtl:
            if current_segment:
                segments.append((current_segment, current_is_rtl))
            current_segment = char
            current_is_rtl = char_is_rtl
        else:
            current_segment += char
    
    # Add the last segment
    if current_segment:
        segments.append((current_segment, current_is_rtl))
    
    return segments

# Define character ranges for RTL scripts
RTL_SCRIPTS = {
    'Arabic': (0x0600, 0x06FF),
    'Arabic Supplement': (0x0750, 0x077F),
    'Arabic Extended-A': (0x08A0, 0x08FF),
    'Arabic Presentation Forms-A': (0xFB50, 0xFDFF),
    'Arabic Presentation Forms-B': (0xFE70, 0xFEFF),
    'Hebrew': (0x0590, 0x05FF),
    'Hebrew Presentation Forms': (0xFB1D, 0xFB4F),
    'Thaana': (0x0780, 0x07BF),  # Dhivehi
    'Nko': (0x07C0, 0x07FF),
    'Samaritan': (0x0800, 0x083F),
    'Mandaic': (0x0840, 0x085F),
    'Syriac': (0x0700, 0x074F),
    'Persian': (0x0600, 0x06FF),  # Uses Arabic script with additional characters
    'Urdu': (0x0600, 0x06FF),     # Uses Arabic script with additional characters
}

# Regex patterns to detect RTL text (combining major RTL scripts)
RTL_PATTERN = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\u0590-\u05FF'
                         r'\uFB50-\uFDFF\uFE70-\uFEFF\uFB1D-\uFB4F\u0780-\u07BF'
                         r'\u07C0-\u07FF\u0800-\u083F\u0840-\u085F\u0700-\u074F]+')

# Threshold for determining if a text is primarily RTL (proportion of RTL characters)
RTL_THRESHOLD = 0.3  # If 30% or more characters are RTL, consider it an RTL text

def is_rtl_char(char: str) -> bool:
    """
    Check if a single character belongs to an RTL script.
    
    Args:
        char: A single Unicode character
        
    Returns:
        True if the character belongs to an RTL script, False otherwise
    """
    if not char or len(char) != 1:
        return False
    
    # Get the Unicode code point
    code_point = ord(char)
    
    # Check if the code point falls within any RTL script range
    for script_range in RTL_SCRIPTS.values():
        if script_range[0] <= code_point <= script_range[1]:
            return True
    
    return False

def is_rtl(text: str) -> bool:
    """
    Determine if a text contains significant RTL content.
    
    This function examines the text to see if it contains a significant 
    proportion of RTL characters to determine if RTL processing is needed.
    
    Args:
        text: The text to check
        
    Returns:
        True if the text contains significant RTL content, False otherwise
    """
    if not text:
        return False
    
    # Quick check using regex pattern
    if RTL_PATTERN.search(text):
        # Count RTL characters
        rtl_count = sum(1 for char in text if is_rtl_char(char))
        non_whitespace_count = sum(1 for char in text if not char.isspace())
        
        # If non_whitespace_count is zero, avoid division by zero
        if non_whitespace_count == 0:
            return False
            
        # Calculate RTL proportion
        rtl_proportion = rtl_count / non_whitespace_count
        
        return rtl_proportion >= RTL_THRESHOLD
    
    return False

def get_text_direction(text: str) -> str:
    """
    Get the primary direction of text ('rtl' or 'ltr').
    
    Args:
        text: The text to analyze
        
    Returns:
        'rtl' if the text is primarily right-to-left, otherwise 'ltr'
    """
    return 'rtl' if detect_rtl_text(text) else 'ltr'

def get_rtl_runs(text: str) -> List[Tuple[bool, str]]:
    """
    Split text into runs of RTL and non-RTL segments.
    
    This is useful for mixed-direction text where only portions need RTL handling.
    
    Args:
        text: The text to process
        
    Returns:
        A list of tuples (is_rtl, segment) where is_rtl is a boolean indicating
        if the segment is RTL, and segment is the text segment
    """
    if not text:
        return []
    
    result = []
    current_rtl = None
    current_segment = ""
    
    for char in text:
        char_rtl = is_rtl_char(char)
        
        # If this is the first character or if direction changed
        if current_rtl is None or current_rtl != char_rtl:
            # Add the previous segment to result if not empty
            if current_segment:
                result.append((current_rtl, current_segment))
                current_segment = ""
            
            # Update current direction
            current_rtl = char_rtl
        
        # Add character to current segment
        current_segment += char
    
    # Add the last segment
    if current_segment:
        result.append((current_rtl, current_segment))
        
    return result

def reorder_text(text: str) -> str:
    """
    Reorder RTL text for proper display.
    
    This function applies the Unicode Bidirectional Algorithm (UBA) to reorder
    text properly for display in environments that don't natively support RTL.
    
    Args:
        text: The text to reorder
        
    Returns:
        The reordered text
    """
    if not text or not detect_rtl_text(text):
        return text
    
    # If bidi support is available, use the libraries
    if HAS_BIDI_SUPPORT:
        try:
            # Reshape Arabic text (connects letters properly)
            reshaped_text = arabic_reshaper.reshape(text)
            # Apply bidirectional algorithm
            display_text = get_display(reshaped_text)
            return display_text
        except Exception as e:
            logger.warning(f"Error during RTL text reordering: {e}. Falling back to basic reordering.")
    
    # Basic fallback for when libraries aren't available
    # This is a simplified approach and won't handle complex cases properly
    runs = get_rtl_runs(text)
    result = ""
    
    for is_rtl, segment in runs:
        if is_rtl:
            # Reverse the RTL segment
            result += segment[::-1]
        else:
            # Keep LTR segment as is
            result += segment
    
    return result

def reorder_words(words: List[str], is_rtl: Optional[bool] = None) -> List[str]:
    """
    Reorder a list of words according to the text direction.
    
    This is useful for cases where words were extracted in visual order
    but need to be put in logical order, or vice versa.
    
    Args:
        words: List of words to reorder
        is_rtl: Whether to treat as RTL text. If None, will detect automatically.
        
    Returns:
        Reordered list of words
    """
    if not words:
        return []
    
    # If RTL not specified, detect from the concatenated words
    if is_rtl is None:
        text = " ".join(words)
        is_rtl = detect_rtl_text(text)
    
    if is_rtl:
        # For RTL text, reverse the word order
        return list(reversed(words))
    
    # For LTR text, keep the original order
    return words

def normalize_rtl_text(text: str) -> str:
    """
    Normalize RTL text by handling common issues in RTL text extraction.
    
    This handles issues like normalization of Arabic/Hebrew characters,
    removing unnecessary control characters, etc.
    
    Args:
        text: The text to normalize
        
    Returns:
        Normalized text
    """
    if not text:
        return text
    
    # Normalize Unicode (NFC form)
    normalized = unicodedata.normalize('NFC', text)
    
    # Remove unwanted control characters
    normalized = re.sub(r'[\u200e\u200f\u061c]', '', normalized)
    
    return normalized

def process_rtl_paragraph(text: str) -> str:
    """
    Process an entire paragraph that may contain RTL text.
    
    This is a convenience function that combines detection, normalization,
    and reordering in one step.
    
    Args:
        text: The paragraph text to process
        
    Returns:
        The processed text, properly normalized and reordered
    """
    if not text:
        return text
    
    # Skip processing if not RTL
    if not detect_rtl_text(text):
        return text
    
    # Normalize the text
    normalized = normalize_rtl_text(text)
    
    # Reorder for proper display
    reordered = reorder_text(normalized)
    
    return reordered

def process_mixed_text(text: str) -> str:
    """
    Process text that may contain both RTL and LTR content.
    
    This function handles mixed-direction text by processing each
    direction segment separately and then combining them.
    
    Args:
        text: The mixed-direction text to process
        
    Returns:
        The processed text with each direction segment properly handled
    """
    if not text:
        return text
    
    # Get runs of RTL and LTR text
    runs = get_rtl_runs(text)
    result = ""
    
    # Process each run according to its direction
    for is_rtl, segment in runs:
        if is_rtl:
            result += process_rtl_paragraph(segment)
        else:
            result += segment
    
    return result

# Additional utility functions

def detect_and_mark_rtl(text: str) -> str:
    """
    Detect RTL segments and mark them with Unicode directional markers.
    
    This is useful for preparing text for rendering systems that
    support directional markers but don't automatically apply RTL rules.
    
    Args:
        text: The text to mark
        
    Returns:
        Text with appropriate Unicode directional markers inserted
    """
    if not text:
        return text
    
    # RLM (Right-to-Left Mark): U+200F
    # LRM (Left-to-Right Mark): U+200E
    
    runs = get_rtl_runs(text)
    result = ""
    
    for is_rtl, segment in runs:
        if is_rtl:
            # Add RLM before and after RTL segment
            result += "\u200F" + segment + "\u200F"
        else:
            # Add LRM before and after LTR segment in RTL context
            if any(r[0] for r in runs):  # If there are any RTL runs
                result += "\u200E" + segment + "\u200E"
            else:
                result += segment
    
    return result
