"""
Language predictor for document language analysis using langdetect.

This predictor uses the langdetect library to detect the primary language of the document text.
"""
import logging

from .base import BasePredictor

try:
    from langdetect import detect, detect_langs
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

logger = logging.getLogger(__name__)

class LanguagePredictor(BasePredictor):
    name = "language"
    description = "Predicts document language using langdetect."

    def analyze(self, document_path: str, min_confidence: float = 0.2, **kwargs):
        if not LANGDETECT_AVAILABLE:
            raise RuntimeError("langdetect library is not available. Please install it to use language detection.")
        try:
            with open(document_path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            logger.error(f"Failed to read document for language detection: {e}")
            raise
        # Use langdetect to get language probabilities
        try:
            langs = detect_langs(text)
            if not langs:
                return {"language": None, "confidence": 0.0}
            best = langs[0]
            lang_code = best.lang
            confidence = best.prob
            if confidence < min_confidence:
                return {"language": lang_code, "confidence": confidence, "note": "Below min_confidence"}
            return {"language": lang_code, "confidence": confidence}
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return {"language": None, "confidence": 0.0, "error": str(e)} 