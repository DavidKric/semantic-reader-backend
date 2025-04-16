"""
Tests for the predictor modules, including RTL utilities and language detection.

WARNING: This test file is using deprecated functionality that will be removed in a future version.
It is maintained only for backward compatibility during the transition to Docling's native capabilities.
"""

import unittest
from unittest.mock import patch, MagicMock
import warnings

# Import RTL utilities (now directly from the __init__.py file)
from papermage_docling.predictors import (
    is_rtl_char, is_rtl, get_text_direction, reorder_words, reorder_text,
    is_rtl_language, get_language_name, detect_language, LanguagePredictor
)


# Suppress deprecation warnings during tests
warnings.filterwarnings("ignore", category=DeprecationWarning)


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
        self.assertTrue(is_rtl("هذا نص باللغة العربية"))
        
        # Test Hebrew text
        self.assertTrue(is_rtl("זה טקסט בעברית"))
        
        # Test mixed text with sufficient RTL
        self.assertTrue(is_rtl("This is mixed with بعض العربية"))
        
        # Test non-RTL text
        self.assertFalse(is_rtl("This is English text"))
        self.assertFalse(is_rtl("1234 5678"))
        
        # Test mixed text with insufficient RTL
        self.assertFalse(is_rtl("English with one ر letter"))
        
        # Test empty text
        self.assertFalse(is_rtl(""))
    
    def test_get_text_direction(self):
        """Test text direction detection."""
        self.assertEqual(get_text_direction("هذا نص باللغة العربية"), "rtl")
        self.assertEqual(get_text_direction("This is English text"), "ltr")
    
    @unittest.skip("Deprecated function that returns unmodified input")
    def test_reorder_words(self):
        """Test word reordering (skipped - deprecated)."""
        pass
    
    @unittest.skip("Deprecated function that returns unmodified input")
    def test_reorder_text_without_bidi(self):
        """Test text reordering (skipped - deprecated)."""
        pass


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
        
        # Unknown language should return formatted unknown
        self.assertTrue("Unknown" in get_language_name('xx'))
    
    @unittest.skip("Deprecated function that always returns 'en'")
    def test_detect_language(self):
        """Test language detection (skipped - deprecated)."""
        pass
    
    def test_language_predictor_class(self):
        """Test the LanguagePredictor class."""
        # Create predictor - should return a stub
        predictor = LanguagePredictor()
        
        # Test that it doesn't raise errors but returns input
        doc = MagicMock()
        result = predictor.process(doc)
        self.assertEqual(result, doc)


if __name__ == '__main__':
    unittest.main()
