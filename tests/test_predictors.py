"""
Tests for the predictor modules, including RTL utilities and language detection.
"""

import unittest
from unittest.mock import patch, MagicMock

# Import RTL utilities
from papermage_docling.predictors.rtl_utils import (
    is_rtl_char, detect_rtl_text, get_text_direction, reorder_words, reorder_text
)
from papermage_docling.predictors.language_predictor import (
    LanguagePredictor, is_rtl_language, get_language_name, detect_language
)


class TestRtlUtils(unittest.TestCase):
    """Tests for RTL text utilities."""
    
    def test_is_rtl_char(self):
        """Test RTL character detection."""
        # Test Arabic characters
        self.assertTrue(is_rtl_char('ا'))  # Arabic alef
        self.assertTrue(is_rtl_char('ب'))  # Arabic baa
        self.assertTrue(is_rtl_char('ت'))  # Arabic taa
        
        # Test Hebrew characters
        self.assertTrue(is_rtl_char('א'))  # Hebrew alef
        self.assertTrue(is_rtl_char('ב'))  # Hebrew bet
        self.assertTrue(is_rtl_char('ג'))  # Hebrew gimel
        
        # Test non-RTL characters
        self.assertFalse(is_rtl_char('a'))  # Latin a
        self.assertFalse(is_rtl_char('1'))  # Digit
        self.assertFalse(is_rtl_char(' '))  # Space
    
    def test_is_rtl(self):
        """Test RTL text detection."""
        # Test Arabic text
        self.assertTrue(detect_rtl_text("هذا نص باللغة العربية"))
        
        # Test Hebrew text
        self.assertTrue(detect_rtl_text("זה טקסט בעברית"))
        
        # Test mixed text with sufficient RTL
        self.assertTrue(detect_rtl_text("This is mixed with بعض العربية"))
        
        # Test non-RTL text
        self.assertFalse(detect_rtl_text("This is English text"))
        self.assertFalse(detect_rtl_text("1234 5678"))
        
        # Test mixed text with insufficient RTL
        self.assertFalse(detect_rtl_text("English with one ر letter"))
        
        # Test empty text
        self.assertFalse(detect_rtl_text(""))
        # Test None
        with self.assertRaises(TypeError):
            detect_rtl_text(None)
    
    def test_get_text_direction(self):
        """Test text direction detection."""
        self.assertEqual(get_text_direction("هذا نص باللغة العربية"), "rtl")
        self.assertEqual(get_text_direction("This is English text"), "ltr")
    
    def test_reorder_words(self):
        """Test word reordering."""
        # Test RTL word reordering
        words = ["كلمة", "أخرى", "باللغة", "العربية"]
        reordered = reorder_words(words, is_rtl=True)
        self.assertEqual(reordered, list(reversed(words)))
        
        # Test LTR word ordering (should remain the same)
        words = ["word", "in", "English"]
        self.assertEqual(reorder_words(words, is_rtl=False), words)
        
        # Test auto-detection
        words = ["كلمة", "أخرى", "باللغة", "العربية"]
        self.assertEqual(reorder_words(words), list(reversed(words)))
        
        # Test empty list
        self.assertEqual(reorder_words([]), [])
    
    @patch('papermage_docling.predictors.rtl_utils.HAS_BIDI_SUPPORT', False)
    def test_reorder_text_without_bidi(self):
        """Test text reordering without bidi support."""
        # Simple RTL text
        text = "هذا نص"
        result = reorder_text(text)
        # Without bidi, should use basic reversal
        self.assertNotEqual(result, text)
        
        # Non-RTL text should remain unchanged
        text = "English text"
        self.assertEqual(reorder_text(text), text)


class TestLanguagePredictor(unittest.TestCase):
    """Tests for language detection."""
    
    def test_is_rtl_language(self):
        """Test RTL language detection by code."""
        # RTL languages
        self.assertTrue(is_rtl_language('ar'))  # Arabic
        self.assertTrue(is_rtl_language('he'))  # Hebrew
        self.assertTrue(is_rtl_language('fa'))  # Persian
        
        # Non-RTL languages
        self.assertFalse(is_rtl_language('en'))  # English
        self.assertFalse(is_rtl_language('fr'))  # French
        self.assertFalse(is_rtl_language('zh'))  # Chinese
        
        # Unknown language
        self.assertFalse(is_rtl_language('xx'))
    
    def test_get_language_name(self):
        """Test language name retrieval."""
        self.assertEqual(get_language_name('en'), 'English')
        self.assertEqual(get_language_name('ar'), 'Arabic')
        self.assertEqual(get_language_name('he'), 'Hebrew')
        
        # Unknown language should return the code
        self.assertEqual(get_language_name('xx'), 'xx')
    
    @patch('papermage_docling.predictors.language_predictor.HAS_LANGDETECT', True)
    @patch('papermage_docling.predictors.language_predictor._detect_with_langdetect')
    def test_detect_language(self, mock_detect):
        """Test language detection."""
        mock_detect.return_value = ('en', 0.95)
        
        # Test with sufficient text
        lang, conf = detect_language("This is a sample English text for testing language detection")
        self.assertEqual(lang, 'en')
        # Confidence might vary slightly based on implementation, just ensure it's reasonable
        self.assertGreater(conf, 0.8)
        
        # Test with very short text
        lang, conf = detect_language("Hi")
        self.assertEqual(lang, 'un')  # Unknown due to short length
        self.assertEqual(conf, 0.0)
    
    @patch('papermage_docling.predictors.language_predictor.detect_rtl_text')
    @patch('papermage_docling.predictors.language_predictor.detect_language')
    def test_language_predictor_class(self, mock_detect, mock_detect_rtl):
        """Test the LanguagePredictor class."""
        # Configure mocks
        mock_detect.return_value = ('en', 0.9)
        mock_detect_rtl.return_value = False
        
        # Create predictor and test basic functionality
        predictor = LanguagePredictor(detect_rtl=True)
        result = predictor.predict_document_language("Sample text")
        
        # Check result structure
        self.assertEqual(result['language'], 'en')
        self.assertEqual(result['language_name'], 'English')
        self.assertAlmostEqual(result['confidence'], 0.9)
        self.assertFalse(result['is_rtl'])
        self.assertEqual(result['additional_languages'], [])
        
        # Test batch prediction
        batch_results = predictor.batch_predict(["Text 1", "Text 2"])
        self.assertEqual(len(batch_results), 2)


if __name__ == '__main__':
    unittest.main()
