"""
Integration tests for RTL processing in the DoclingPdfParser.
"""

import unittest
from unittest.mock import patch, MagicMock
import io

from papermage_docling.parsers import DoclingPdfParser


class TestRtlIntegration(unittest.TestCase):
    """Integration tests for RTL functionality in PDF parsing."""
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    def test_rtl_processing_pipeline(self, mock_base_parser):
        """Test the full RTL processing pipeline."""
        # Create a mock PDF document with RTL content
        mock_page = MagicMock()
        mock_page.lines = [
            MagicMock(text="هذا نص باللغة العربية", words=[]),  # Arabic text
            MagicMock(text="This is English text", words=[]),    # English text
            MagicMock(text="זה טקסט בעברית", words=[]),         # Hebrew text
            MagicMock(text="Mixed text with العربية", words=[])  # Mixed text
        ]
        
        mock_pdf_doc = MagicMock()
        mock_pdf_doc.pages = [mock_page]
        mock_pdf_doc.metadata = {}
        
        # Set up parser to return our mock document
        parser = DoclingPdfParser(
            detect_rtl=True,
            enable_language_detection=True
        )
        parser.pdf_parser.load.return_value = mock_pdf_doc
        
        # Mock language detection to identify Arabic as the main language
        with patch('papermage_docling.predictors.language_predictor.detect_language') as mock_detect:
            mock_detect.return_value = ('ar', 0.9)  # Arabic with high confidence
            
            # Parse the "document"
            with patch.object(parser, '_validate_pdf_path', return_value="test.pdf"):
                result = parser.parse("test.pdf", output_format="docling")
        
        # Verify RTL was processed
        self.assertTrue(result.metadata.get('has_rtl_content', False))
        self.assertTrue(result.metadata.get('is_rtl_language', False))
        self.assertEqual(result.metadata.get('language'), 'ar')
        
        # Check that RTL lines were processed
        rtl_lines_count = result.metadata.get('rtl_lines_count', 0)
        self.assertGreater(rtl_lines_count, 0)
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    def test_mixed_language_document(self, mock_base_parser):
        """Test processing of a document with mixed languages."""
        # Create mock document with mixed language content
        mock_page1 = MagicMock()
        mock_page1.lines = [
            MagicMock(text="English content section header", words=[]),
            MagicMock(text="This is a paragraph in English with some فارسی text.", words=[]),
            MagicMock(text="Another paragraph in English.", words=[])
        ]
        
        mock_page2 = MagicMock()
        mock_page2.lines = [
            MagicMock(text="بخش محتوای فارسی", words=[]),  # Persian section header
            MagicMock(text="این یک پاراگراف به زبان فارسی است.", words=[]),  # Persian paragraph
            MagicMock(text="این پاراگراف دیگری به زبان فارسی است با some English text.", words=[])  # Mixed
        ]
        
        mock_pdf_doc = MagicMock()
        mock_pdf_doc.pages = [mock_page1, mock_page2]
        mock_pdf_doc.metadata = {}
        
        # Set up parser to return our mock document
        parser = DoclingPdfParser(
            detect_rtl=True,
            enable_language_detection=True
        )
        parser.pdf_parser.load.return_value = mock_pdf_doc
        
        # Mock language detection to identify as primarily English with Persian as secondary
        with patch('papermage_docling.predictors.language_predictor.LanguagePredictor.predict_document_language') as mock_predict:
            mock_predict.return_value = {
                'language': 'en',
                'language_name': 'English',
                'confidence': 0.7,
                'is_rtl': False,
                'additional_languages': [
                    {
                        'language': 'fa',
                        'language_name': 'Persian',
                        'proportion': 0.3,
                        'is_rtl': True
                    }
                ]
            }
            
            # Parse the "document"
            with patch.object(parser, '_validate_pdf_path', return_value="test.pdf"):
                result = parser.parse("test.pdf", output_format="docling")
        
        # Verify mixed language detection
        self.assertEqual(result.metadata.get('language'), 'en')
        self.assertFalse(result.metadata.get('is_rtl_language', True))
        
        # Check that additional languages were detected
        additional_langs = result.metadata.get('additional_languages', [])
        self.assertEqual(len(additional_langs), 1)
        self.assertEqual(additional_langs[0]['language'], 'fa')
        self.assertTrue(additional_langs[0]['is_rtl'])
        
        # Check that some RTL content was still processed
        self.assertTrue(result.metadata.get('has_rtl_content', False))
        rtl_lines_count = result.metadata.get('rtl_lines_count', 0)
        self.assertGreater(rtl_lines_count, 0)
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    def test_rtl_disabled(self, mock_base_parser):
        """Test that RTL processing can be disabled."""
        # Create a mock PDF document with RTL content
        mock_page = MagicMock()
        mock_page.lines = [
            MagicMock(text="هذا نص باللغة العربية", words=[]),  # Arabic text
            MagicMock(text="זה טקסט בעברית", words=[])         # Hebrew text
        ]
        
        mock_pdf_doc = MagicMock()
        mock_pdf_doc.pages = [mock_page]
        mock_pdf_doc.metadata = {}
        
        # Set up parser with RTL detection disabled
        parser = DoclingPdfParser(
            detect_rtl=False,
            enable_language_detection=True
        )
        parser.pdf_parser.load.return_value = mock_pdf_doc
        
        # Mock language detection to identify Arabic
        with patch('papermage_docling.predictors.language_predictor.detect_language') as mock_detect:
            mock_detect.return_value = ('ar', 0.9)  # Arabic with high confidence
            
            # Parse the "document"
            with patch.object(parser, '_validate_pdf_path', return_value="test.pdf"):
                result = parser.parse("test.pdf", output_format="docling")
        
        # Verify language was detected
        self.assertEqual(result.metadata.get('language'), 'ar')
        
        # Verify RTL processing was not applied
        self.assertNotIn('has_rtl_content', result.metadata)
        self.assertNotIn('rtl_lines_count', result.metadata)
        
        # Original text should be unchanged
        self.assertEqual(result.pages[0].lines[0].text, "هذا نص باللغة العربية")


if __name__ == '__main__':
    unittest.main() 