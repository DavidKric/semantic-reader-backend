"""
Language detection utilities for Docling.

This module provides functionality for detecting document languages, which is 
particularly useful for identifying right-to-left (RTL) languages.
"""

import logging
from typing import Dict, List, Optional, Union, Tuple
import re

# Import langdetect for language identification
try:
    import langdetect
    from langdetect import DetectorFactory
    # Set seed for deterministic results
    DetectorFactory.seed = 0
    HAS_LANGDETECT = True
except ImportError:
    HAS_LANGDETECT = False
    logging.warning(
        "langdetect library not found. Language detection will be limited. "
        "Install with: pip install langdetect"
    )

# Optional import for improved language detection (fastText)
try:
    import fasttext
    HAS_FASTTEXT = True
except ImportError:
    HAS_FASTTEXT = False
    logging.warning(
        "fasttext library not found. Using simpler language detection. "
        "For better results, install fasttext: pip install fasttext"
    )

from papermage_docling.predictors.rtl_utils import (
    contains_rtl_characters, detect_rtl_text
)

logger = logging.getLogger(__name__)

# Define RTL languages by ISO code
RTL_LANGUAGES = {
    'ar': 'Arabic',
    'arc': 'Aramaic',
    'dv': 'Dhivehi',
    'fa': 'Persian',
    'ha': 'Hausa',
    'he': 'Hebrew',
    'khw': 'Khowar',
    'ks': 'Kashmiri',
    'ku': 'Kurdish',
    'ps': 'Pashto',
    'ur': 'Urdu',
    'yi': 'Yiddish',
}

# Language mapping from ISO code to human-readable name
LANGUAGE_NAMES = {
    'ar': 'Arabic',
    'bg': 'Bulgarian',
    'cs': 'Czech',
    'da': 'Danish',
    'de': 'German',
    'el': 'Greek',
    'en': 'English',
    'es': 'Spanish',
    'et': 'Estonian',
    'fa': 'Persian',
    'fi': 'Finnish',
    'fr': 'French',
    'he': 'Hebrew',
    'hi': 'Hindi',
    'hr': 'Croatian',
    'hu': 'Hungarian',
    'id': 'Indonesian',
    'it': 'Italian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'lt': 'Lithuanian',
    'lv': 'Latvian',
    'nl': 'Dutch',
    'no': 'Norwegian',
    'pl': 'Polish',
    'pt': 'Portuguese',
    'ro': 'Romanian',
    'ru': 'Russian',
    'sk': 'Slovak',
    'sl': 'Slovenian',
    'sq': 'Albanian',
    'sv': 'Swedish',
    'th': 'Thai',
    'tr': 'Turkish',
    'uk': 'Ukrainian',
    'ur': 'Urdu',
    'vi': 'Vietnamese',
    'zh': 'Chinese',
}

# FastText language detection model
_FASTTEXT_MODEL = None


def _load_fasttext_model():
    """Load and cache the FastText language detection model."""
    global _FASTTEXT_MODEL
    if HAS_FASTTEXT and _FASTTEXT_MODEL is None:
        try:
            # Try to download the model if not already present
            try:
                _FASTTEXT_MODEL = fasttext.load_model('lid.176.ftz')
            except Exception:
                import urllib.request
                import os
                
                model_path = os.path.join(os.path.expanduser('~'), '.cache', 'fasttext', 'lid.176.ftz')
                os.makedirs(os.path.dirname(model_path), exist_ok=True)
                
                logger.info("Downloading FastText language detection model...")
                urllib.request.urlretrieve(
                    'https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz', 
                    model_path
                )
                _FASTTEXT_MODEL = fasttext.load_model(model_path)
                logger.info("FastText model downloaded and loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load FastText model: {e}")
            _FASTTEXT_MODEL = None
    return _FASTTEXT_MODEL


def is_rtl_language(lang_code: str) -> bool:
    """
    Check if a language is a right-to-left language.
    
    Args:
        lang_code: ISO 639-1/3 language code (e.g., 'ar' for Arabic)
        
    Returns:
        True if the language is RTL, False otherwise
    """
    return lang_code in RTL_LANGUAGES


def detect_language(text: str, method: str = 'auto') -> Tuple[str, float]:
    """
    Detect the language of a given text.
    
    Args:
        text: The text to analyze
        method: Detection method ('langdetect', 'fasttext', or 'auto')
        
    Returns:
        Tuple of (language_code, confidence)
    """
    if not text or len(text.strip()) < 10:
        return ('un', 0.0)  # Unknown language for very short text
    
    # Clean the text to improve detection
    clean_text = re.sub(r'\s+', ' ', text)
    clean_text = re.sub(r'[0-9]+', '', clean_text)
    clean_text = clean_text.strip()
    
    # Handle very short text after cleaning
    if len(clean_text) < 10:
        # If text has RTL characters, default to Arabic (most common RTL language)
        if is_rtl(clean_text):
            return ('ar', 0.6)  # Moderate confidence
        return ('en', 0.5)  # Default to English with low confidence
    
    # Use the appropriate detection method
    if method == 'langdetect' or (method == 'auto' and not HAS_FASTTEXT):
        return _detect_with_langdetect(clean_text)
    elif method == 'fasttext' or (method == 'auto' and HAS_FASTTEXT):
        return _detect_with_fasttext(clean_text)
    else:
        logger.warning(f"Unknown language detection method: {method}. Using fallback.")
        # Fallback to langdetect if available
        if HAS_LANGDETECT:
            return _detect_with_langdetect(clean_text)
        # Fallback to character-based heuristic
        if is_rtl(clean_text):
            return ('ar', 0.6)  # Default RTL to Arabic with moderate confidence
        return ('en', 0.5)  # Default to English with low confidence


def _detect_with_langdetect(text: str) -> Tuple[str, float]:
    """Use langdetect to identify the language."""
    if not HAS_LANGDETECT:
        logger.warning("langdetect not available, returning default")
        return ('en', 0.0)
    
    try:
        # Get language probabilities
        probs = langdetect.detect_langs(text)
        if probs:
            lang_code = probs[0].lang
            confidence = probs[0].prob
            return (lang_code, confidence)
        return ('un', 0.0)
    except Exception as e:
        logger.warning(f"Language detection failed: {e}")
        return ('un', 0.0)


def _detect_with_fasttext(text: str) -> Tuple[str, float]:
    """Use Facebook's FastText to identify the language."""
    model = _load_fasttext_model()
    if not model:
        logger.warning("FastText model not available, falling back to langdetect")
        return _detect_with_langdetect(text)
    
    try:
        # Get language prediction and confidence
        predictions = model.predict(text.replace('\n', ' '))
        lang_code = predictions[0][0].replace('__label__', '')
        confidence = float(predictions[1][0])
        return (lang_code, confidence)
    except Exception as e:
        logger.warning(f"FastText language detection failed: {e}")
        return _detect_with_langdetect(text)


def get_language_name(lang_code: str) -> str:
    """
    Get the human-readable language name from a language code.
    
    Args:
        lang_code: ISO 639-1/3 language code
        
    Returns:
        Human-readable language name or the original code if not found
    """
    # Strip any prefix (e.g., '__label__' from FastText)
    if '__label__' in lang_code:
        lang_code = lang_code.replace('__label__', '')
    
    return LANGUAGE_NAMES.get(lang_code, lang_code)


def analyze_document_languages(text: str, min_chunk_size: int = 200) -> Dict[str, float]:
    """
    Analyze a document to detect possibly multiple languages.
    
    Splits the document into chunks and analyzes each chunk separately.
    
    Args:
        text: The document text
        min_chunk_size: Minimum chunk size to analyze
        
    Returns:
        Dictionary of {language_code: proportion} sorted by proportion
    """
    if not text:
        return {}
    
    # Split text into meaningful chunks
    chunks = _split_into_chunks(text, min_chunk_size)
    
    # Detect language of each chunk
    lang_votes = {}
    
    for chunk in chunks:
        if len(chunk.strip()) < min_chunk_size // 2:
            continue
            
        lang_code, confidence = detect_language(chunk)
        
        # Only count if confidence is reasonable
        if confidence > 0.5:
            lang_votes[lang_code] = lang_votes.get(lang_code, 0) + 1
    
    # Convert to proportions
    total_votes = sum(lang_votes.values())
    if total_votes == 0:
        return {}
        
    lang_proportions = {
        lang: count / total_votes 
        for lang, count in lang_votes.items()
    }
    
    # Sort by proportion (descending)
    return dict(sorted(
        lang_proportions.items(), 
        key=lambda item: item[1], 
        reverse=True
    ))


def _split_into_chunks(text: str, chunk_size: int) -> List[str]:
    """
    Split text into reasonable chunks for language analysis.
    
    Tries to split on paragraph boundaries when possible.
    
    Args:
        text: Text to split
        chunk_size: Target chunk size
        
    Returns:
        List of text chunks
    """
    # First try to split on paragraphs
    paragraphs = re.split(r'\n\s*\n', text)
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk += "\n" + para if current_chunk else para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            
            # If paragraph is longer than chunk_size, split it further
            if len(para) > chunk_size:
                # Split on sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                current_chunk = ""
                
                for sent in sentences:
                    if len(current_chunk) + len(sent) <= chunk_size:
                        current_chunk += " " + sent if current_chunk else sent
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        
                        # If sentence is longer than chunk_size, add it as is
                        if len(sent) > chunk_size:
                            # Further split into fixed-size chunks as a last resort
                            sent_chunks = [sent[i:i+chunk_size] for i in range(0, len(sent), chunk_size)]
                            chunks.extend(sent_chunks)
                            current_chunk = ""
                        else:
                            current_chunk = sent
            else:
                current_chunk = para
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


class LanguagePredictor:
    """
    Language prediction for documents and text segments.
    
    This class provides methods to detect the primary language and
    multiple languages in documents, with optional RTL detection.
    """
    
    def __init__(self, detect_rtl: bool = True, method: str = 'auto'):
        """
        Initialize the language predictor.
        
        Args:
            detect_rtl: Whether to apply RTL-specific detection logic
            method: Language detection method ('auto', 'langdetect', 'fasttext')
        """
        self.detect_rtl = detect_rtl
        self.method = method
        
        if method == 'fasttext' and not HAS_FASTTEXT:
            logger.warning("FastText requested but not available. Falling back to other methods.")
            self.method = 'auto'
        
        logger.info(f"Initialized LanguagePredictor (detect_rtl: {detect_rtl}, method: {self.method})")
    
    def predict_document_language(self, text: str) -> Dict[str, any]:
        """
        Predict the primary language of a document.
        
        Args:
            text: Document text
            
        Returns:
            Dictionary with language information:
            {
                'language': str (ISO code),
                'language_name': str (human-readable name), 
                'confidence': float,
                'is_rtl': bool,
                'additional_languages': list of dicts (if multiple detected)
            }
        """
        if not text:
            return {
                'language': 'un',
                'language_name': 'Unknown',
                'confidence': 0.0,
                'is_rtl': False,
                'additional_languages': []
            }
        
        # First detect primary language
        lang_code, confidence = detect_language(text, method=self.method)
        is_rtl_lang = is_rtl_language(lang_code)
        
        # For RTL languages with low confidence, verify with character-based detection
        if self.detect_rtl and is_rtl_lang and confidence < 0.7:
            has_rtl_chars = detect_rtl_text(text)
            
            # If character detection doesn't agree with language detection,
            # adjust results based on which has stronger evidence
            if not has_rtl_chars and confidence < 0.6:
                # Language detected as RTL but no RTL characters and low confidence
                # Try to detect again with langdetect as backup
                if self.method != 'langdetect' and HAS_LANGDETECT:
                    lang_code, confidence = _detect_with_langdetect(text)
                    is_rtl_lang = is_rtl_language(lang_code)
        
        # Check for multiple languages
        additional_languages = []
        lang_proportions = analyze_document_languages(text)
        
        # Remove the primary language from additional languages
        if lang_code in lang_proportions:
            del lang_proportions[lang_code]
        
        # Only report additional languages with significant presence
        for additional_lang, proportion in lang_proportions.items():
            if proportion > 0.15:  # At least 15% of document
                additional_languages.append({
                    'language': additional_lang,
                    'language_name': get_language_name(additional_lang),
                    'proportion': proportion,
                    'is_rtl': is_rtl_language(additional_lang)
                })
        
        return {
            'language': lang_code,
            'language_name': get_language_name(lang_code),
            'confidence': confidence,
            'is_rtl': is_rtl_lang,
            'additional_languages': additional_languages
        }
    
    def predict_text_segment_language(self, text: str) -> Dict[str, any]:
        """
        Predict the language of a smaller text segment.
        
        Similar to predict_document_language but optimized for shorter texts.
        
        Args:
            text: Text segment to analyze
            
        Returns:
            Dictionary with language information
        """
        if not text or len(text.strip()) < 5:
            return {
                'language': 'un',
                'language_name': 'Unknown',
                'confidence': 0.0,
                'is_rtl': False
            }
        
        # For short segments, check if it has RTL characters first
        if self.detect_rtl and detect_rtl_text(text):
            # For very short segments with RTL characters, default to Arabic
            if len(text.strip()) < 20:
                return {
                    'language': 'ar',  # Default to Arabic for short RTL segments
                    'language_name': 'Arabic',
                    'confidence': 0.6,
                    'is_rtl': True
                }
        
        # Detect language
        lang_code, confidence = detect_language(text, method=self.method)
        is_rtl_lang = is_rtl_language(lang_code)
        
        return {
            'language': lang_code,
            'language_name': get_language_name(lang_code),
            'confidence': confidence,
            'is_rtl': is_rtl_lang
        }
    
    def batch_predict(self, texts: List[str]) -> List[Dict[str, any]]:
        """
        Predict languages for multiple text segments in batch.
        
        Args:
            texts: List of text segments
            
        Returns:
            List of language prediction dictionaries
        """
        return [self.predict_text_segment_language(text) for text in texts]


def get_language_predictor() -> LanguagePredictor:
    """
    Get a default language predictor instance.
    
    Returns:
        LanguagePredictor: A configured language predictor
    """
    return LanguagePredictor(detect_rtl=True, method='auto')
