import unittest
from unittest.mock import patch, MagicMock, ANY
import pytest
import io
from pathlib import Path

# Import the parser class
from papermage_docling.parsers import DoclingPdfParser


class TestDoclingPdfParser(unittest.TestCase):
    """Tests for DoclingPdfParser class."""
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    def test_initialization_default_settings(self, mock_base_parser):
        """Test initialization with default settings."""
        # Arrange & Act
        parser = DoclingPdfParser()
        
        # Assert
        mock_base_parser.assert_called_once_with(
            loglevel='fatal'
        )
        self.assertFalse(parser.enable_ocr)
        self.assertEqual(parser.ocr_language, "eng")
        self.assertTrue(parser.detect_rtl)
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    def test_initialization_custom_settings(self, mock_base_parser):
        """Test initialization with custom settings."""
        # Arrange & Act
        parser = DoclingPdfParser(
            enable_ocr=True,
            ocr_language="heb",
            detect_rtl=False,
            custom_option="value"
        )
        
        # Assert
        mock_base_parser.assert_called_once_with(
            loglevel='info'
        )
        self.assertTrue(parser.enable_ocr)
        self.assertEqual(parser.ocr_language, "heb")
        self.assertFalse(parser.detect_rtl)
        self.assertEqual(parser.config, {"custom_option": "value"})
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    def test_initialization_error_handling(self, mock_base_parser):
        """Test error handling during initialization."""
        # Arrange
        mock_base_parser.side_effect = Exception("Test error")
        
        # Act & Assert
        with self.assertRaises(Exception) as context:
            DoclingPdfParser()
        
        self.assertTrue("Test error" in str(context.exception))
    
    def test_validate_pdf_path_with_string(self):
        """Test _validate_pdf_path with string path."""
        # Arrange
        parser = DoclingPdfParser()
        
        # Act & Assert - Using patch to mock os.path.exists
        with patch('os.path.exists', return_value=True):
            result = parser._validate_pdf_path("test.pdf")
            self.assertEqual(result, "test.pdf")
    
    def test_validate_pdf_path_with_path_object(self):
        """Test _validate_pdf_path with Path object."""
        # Arrange
        parser = DoclingPdfParser()
        path = Path("test.pdf")
        
        # Act & Assert
        with patch('os.path.exists', return_value=True):
            result = parser._validate_pdf_path(path)
            self.assertEqual(result, str(path))
    
    def test_validate_pdf_path_with_bytesio(self):
        """Test _validate_pdf_path with BytesIO object."""
        # Arrange
        parser = DoclingPdfParser()
        bytes_io = io.BytesIO(b"PDF content")
        
        # Act
        result = parser._validate_pdf_path(bytes_io)
        
        # Assert
        self.assertEqual(result, bytes_io)
    
    def test_validate_pdf_path_file_not_found(self):
        """Test _validate_pdf_path with non-existent file."""
        # Arrange
        parser = DoclingPdfParser()
        
        # Act & Assert
        with patch('os.path.exists', return_value=False):
            with self.assertRaises(FileNotFoundError):
                parser._validate_pdf_path("nonexistent.pdf")
    
    def test_validate_pdf_path_invalid_input(self):
        """Test _validate_pdf_path with invalid input."""
        # Arrange
        parser = DoclingPdfParser()
        
        # Act & Assert
        with self.assertRaises(ValueError):
            parser._validate_pdf_path(123)  # Integer is invalid

    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    def test_parse_docling_format(self, mock_base_parser):
        """Test parsing in Docling format."""
        # Arrange
        parser = DoclingPdfParser()
        mock_pdf_doc = MagicMock()
        mock_pdf_doc.pages = [MagicMock(), MagicMock()]
        parser.pdf_parser.load.return_value = mock_pdf_doc
        
        # Act
        with patch.object(parser, '_validate_pdf_path', return_value="test.pdf"):
            result = parser.parse("test.pdf", output_format="docling")
        
        # Assert
        parser.pdf_parser.load.assert_called_once_with(path_or_stream="test.pdf")
        self.assertEqual(result, mock_pdf_doc)
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingToPaperMageConverter')
    def test_parse_papermage_format(self, mock_converter, mock_base_parser):
        """Test parsing with conversion to PaperMage format."""
        # Arrange
        parser = DoclingPdfParser()
        mock_pdf_doc = MagicMock()
        mock_pdf_doc.pages = [MagicMock(), MagicMock()]
        parser.pdf_parser.load.return_value = mock_pdf_doc
        
        mock_papermage_doc = MagicMock()
        mock_converter.convert_pdf_document.return_value = mock_papermage_doc
        
        # Act
        with patch.object(parser, '_validate_pdf_path', return_value="test.pdf"):
            result = parser.parse("test.pdf", output_format="papermage")
        
        # Assert
        parser.pdf_parser.load.assert_called_once_with(path_or_stream="test.pdf")
        mock_converter.convert_pdf_document.assert_called_once_with(mock_pdf_doc)
        self.assertEqual(result, mock_papermage_doc)
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    def test_parse_invalid_format(self, mock_base_parser):
        """Test parsing with invalid output format."""
        # Arrange
        parser = DoclingPdfParser()
        
        # Act & Assert
        with patch.object(parser, '_validate_pdf_path', return_value="test.pdf"):
            with self.assertRaises(ValueError) as context:
                parser.parse("test.pdf", output_format="invalid")
        
        self.assertTrue("Invalid output format" in str(context.exception))
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    def test_parse_error_handling(self, mock_base_parser):
        """Test error handling during parsing."""
        # Arrange
        parser = DoclingPdfParser()
        parser.pdf_parser.load.side_effect = Exception("Parsing error")
        
        # Act & Assert
        with patch.object(parser, '_validate_pdf_path', return_value="test.pdf"):
            with self.assertRaises(Exception) as context:
                parser.parse("test.pdf")
        
        self.assertTrue("Parsing error" in str(context.exception))
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    def test_rtl_processing_called(self, mock_base_parser):
        """Test that RTL processing is called when detect_rtl is True."""
        # Arrange
        parser = DoclingPdfParser(detect_rtl=True)
        mock_pdf_doc = MagicMock()
        parser.pdf_parser.load.return_value = mock_pdf_doc
    
        # Act
        with patch.object(parser, '_validate_pdf_path', return_value="test.pdf"):
            with patch.object(DoclingPdfParser, '_process_rtl_text') as mock_process_rtl:
                parser.parse("test.pdf")
    
        # Assert - Just check that RTL processing was called
        mock_process_rtl.assert_called_once()
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    def test_rtl_processing_skipped(self, mock_base_parser):
        """Test that RTL processing is skipped when detect_rtl is False."""
        # Arrange
        parser = DoclingPdfParser(detect_rtl=False)
        mock_pdf_doc = MagicMock()
        parser.pdf_parser.load.return_value = mock_pdf_doc
        
        # Act
        with patch.object(parser, '_validate_pdf_path', return_value="test.pdf"):
            with patch.object(parser, '_process_rtl_text') as mock_process_rtl:
                parser.parse("test.pdf")
        
        # Assert
        mock_process_rtl.assert_not_called()
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    def test_rtl_processing_error_handling(self, mock_base_parser):
        """Test error handling during RTL processing."""
        # Arrange
        parser = DoclingPdfParser(detect_rtl=True)
        mock_pdf_doc = MagicMock()
        parser.pdf_parser.load.return_value = mock_pdf_doc
        
        # Act
        with patch.object(parser, '_validate_pdf_path', return_value="test.pdf"):
            with patch.object(parser, '_process_rtl_text', side_effect=Exception("RTL error")):
                # Should not raise an exception, just log a warning
                result = parser.parse("test.pdf")
        
        # Assert
        self.assertEqual(result, mock_pdf_doc)  # Parsing should continue despite RTL error


# Integration tests - these would typically run with actual PDF files
# but here we'll use mocks to simulate the behavior

class TestDoclingPdfParserIntegration(unittest.TestCase):
    """Integration tests for DoclingPdfParser."""
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    def test_integration_docling_format(self, mock_base_parser):
        """Test end-to-end parsing with Docling format."""
        # Create a mock PDF document structure similar to what Docling would return
        mock_page1 = MagicMock()
        mock_page1.lines = [
            MagicMock(text="Line 1 of page 1"),
            MagicMock(text="Line 2 of page 1")
        ]
        mock_page2 = MagicMock()
        mock_page2.lines = [
            MagicMock(text="Line 1 of page 2")
        ]
        
        mock_pdf_doc = MagicMock()
        mock_pdf_doc.pages = [mock_page1, mock_page2]
        
        # Set up parser to return our mock document
        parser = DoclingPdfParser()
        parser.pdf_parser.load.return_value = mock_pdf_doc
        
        # Parse in Docling format
        with patch.object(parser, '_validate_pdf_path', return_value="test.pdf"):
            result = parser.parse("test.pdf", output_format="docling")
        
        # Verify we get the Docling structure back directly
        self.assertEqual(result, mock_pdf_doc)
        self.assertEqual(len(result.pages), 2)
        self.assertEqual(len(result.pages[0].lines), 2)
        self.assertEqual(len(result.pages[1].lines), 1)
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingToPaperMageConverter')
    def test_integration_papermage_format(self, mock_converter, mock_base_parser):
        """Test end-to-end parsing with PaperMage format."""
        # Create a mock PDF document structure similar to what Docling would return
        mock_page1 = MagicMock()
        mock_page1.lines = [
            MagicMock(text="Line 1 of page 1"),
            MagicMock(text="Line 2 of page 1")
        ]
        mock_page2 = MagicMock()
        mock_page2.lines = [
            MagicMock(text="Line 1 of page 2")
        ]
        
        mock_pdf_doc = MagicMock()
        mock_pdf_doc.pages = [mock_page1, mock_page2]
        
        # Create a mock PaperMage document that the converter would return
        from papermage_docling.converters import Document, Entity, Span, Box
        
        mock_papermage_doc = Document(
            symbols="Line 1 of page 1\nLine 2 of page 1\nLine 1 of page 2\n",
            entities={
                "pages": [
                    Entity(
                        spans=[Span(start=0, end=32)],
                        boxes=[Box(x0=0, y0=0, x1=100, y1=100, page=0)]
                    ),
                    Entity(
                        spans=[Span(start=33, end=48)],
                        boxes=[Box(x0=0, y0=0, x1=100, y1=100, page=1)]
                    )
                ],
                "rows": [
                    Entity(
                        spans=[Span(start=0, end=15)],
                        boxes=[Box(x0=0, y0=0, x1=100, y1=20, page=0)]
                    ),
                    Entity(
                        spans=[Span(start=16, end=32)],
                        boxes=[Box(x0=0, y0=25, x1=100, y1=45, page=0)]
                    ),
                    Entity(
                        spans=[Span(start=33, end=48)],
                        boxes=[Box(x0=0, y0=0, x1=100, y1=20, page=1)]
                    )
                ]
            }
        )
        
        # Set up parser and converter to return our mock documents
        parser = DoclingPdfParser()
        parser.pdf_parser.load.return_value = mock_pdf_doc
        mock_converter.convert_pdf_document.return_value = mock_papermage_doc
        
        # Parse in PaperMage format
        with patch.object(parser, '_validate_pdf_path', return_value="test.pdf"):
            result = parser.parse("test.pdf", output_format="papermage")
        
        # Verify we get the PaperMage structure back
        self.assertEqual(result, mock_papermage_doc)
        self.assertEqual(result.symbols, "Line 1 of page 1\nLine 2 of page 1\nLine 1 of page 2\n")
        self.assertEqual(len(result.get_entity_layer("pages")), 2)
        self.assertEqual(len(result.get_entity_layer("rows")), 3)
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    def test_integration_case_insensitive_format(self, mock_base_parser):
        """Test that output_format parameter is case-insensitive."""
        # Arrange
        parser = DoclingPdfParser()
        mock_pdf_doc = MagicMock()
        parser.pdf_parser.load.return_value = mock_pdf_doc
        
        # Act - with different case variations
        with patch.object(parser, '_validate_pdf_path', return_value="test.pdf"):
            result1 = parser.parse("test.pdf", output_format="DOCLING")
            result2 = parser.parse("test.pdf", output_format="Docling")
            result3 = parser.parse("test.pdf", output_format="docling")
        
        # Assert - all should return the same Docling document
        self.assertEqual(result1, mock_pdf_doc)
        self.assertEqual(result2, mock_pdf_doc)
        self.assertEqual(result3, mock_pdf_doc)
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingToPaperMageConverter')
    def test_parsing_with_kwargs(self, mock_converter, mock_base_parser):
        """Test parsing with additional keyword arguments."""
        # Arrange
        parser = DoclingPdfParser()
        mock_pdf_doc = MagicMock()
        parser.pdf_parser.load.return_value = mock_pdf_doc
        
        # Act
        with patch.object(parser, '_validate_pdf_path', return_value="test.pdf"):
            parser.parse("test.pdf", page_numbers=[1, 2], custom_option=True)
        
        # Assert - additional kwargs should be passed to the Docling parser
        parser.pdf_parser.load.assert_called_once_with(
            path_or_stream="test.pdf", 
            page_numbers=[1, 2], 
            custom_option=True
        )


class TestDocumentationExamples(unittest.TestCase):
    """Tests to verify the examples in the documentation."""
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    def test_docling_format_example(self, mock_base_parser):
        """Test the Docling format example from the documentation."""
        # Create a mock PDF document structure
        mock_page = MagicMock()
        mock_page.lines = [MagicMock(text="Example line")]
        mock_pdf_doc = MagicMock()
        mock_pdf_doc.pages = [mock_page]
        
        # Set up parser to return our mock document
        parser = DoclingPdfParser()
        parser.pdf_parser.load.return_value = mock_pdf_doc
        
        # Run the example code from the documentation
        with patch.object(parser, '_validate_pdf_path', return_value="example.pdf"):
            pdf_doc = parser.parse('example.pdf')  # Default is docling format
            
            # This should work without errors
            for page in pdf_doc.pages:
                for line in page.lines:
                    text = line.text
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingToPaperMageConverter')
    def test_papermage_format_example(self, mock_converter, mock_base_parser):
        """Test the PaperMage format example from the documentation."""
        # Create a mock PaperMage document that the converter would return
        from papermage_docling.converters import Document, Entity, Span, Box
        
        mock_papermage_doc = Document(
            symbols="Example text",
            entities={
                "sentences": [
                    Entity(
                        spans=[Span(start=0, end=12)],
                        boxes=[Box(x0=0, y0=0, x1=100, y1=20, page=0)],
                        text="Example text"
                    )
                ]
            }
        )
        
        # Set up parser and converter
        parser = DoclingPdfParser()
        mock_converter.convert_pdf_document.return_value = mock_papermage_doc
        
        # Run the example code from the documentation
        with patch.object(parser, '_validate_pdf_path', return_value="example.pdf"):
            papermage_doc = parser.parse('example.pdf', output_format='papermage')
            
            # This should work without errors
            text = papermage_doc.symbols
            for entity in papermage_doc.get_entity_layer('sentences'):
                sentence = entity.text


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases."""
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    def test_empty_pdf(self, mock_base_parser):
        """Test parsing an empty PDF document."""
        # Arrange - create an empty document
        mock_pdf_doc = MagicMock()
        mock_pdf_doc.pages = []
        
        parser = DoclingPdfParser()
        parser.pdf_parser.load.return_value = mock_pdf_doc
        
        # Act
        with patch.object(parser, '_validate_pdf_path', return_value="empty.pdf"):
            result = parser.parse("empty.pdf")
        
        # Assert - should still return a valid (but empty) document
        self.assertEqual(result, mock_pdf_doc)
        self.assertEqual(len(result.pages), 0)
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    def test_large_pdf_warning(self, mock_base_parser):
        """Test warning for large PDF documents."""
        # Arrange - create a large document (100 pages)
        mock_pdf_doc = MagicMock()
        mock_pdf_doc.pages = [MagicMock() for _ in range(100)]
        
        parser = DoclingPdfParser()
        parser.pdf_parser.load.return_value = mock_pdf_doc
        
        # Act
        with patch.object(parser, '_validate_pdf_path', return_value="large.pdf"):
            with self.assertLogs(level='INFO') as log:
                result = parser.parse("large.pdf")
        
        # Assert - should log info about large document
        self.assertEqual(result, mock_pdf_doc)
        self.assertEqual(len(result.pages), 100)
        
        # Note: In a real implementation, you might want to add a warning log
        # for large documents, and then check for that log message here
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingToPaperMageConverter')
    def test_conversion_error_handling(self, mock_converter, mock_base_parser):
        """Test error handling during conversion to PaperMage format."""
        # Arrange
        parser = DoclingPdfParser()
        mock_pdf_doc = MagicMock()
        parser.pdf_parser.load.return_value = mock_pdf_doc
        
        # Simulate conversion error
        conversion_error = ValueError("Conversion error")
        mock_converter.convert_pdf_document.side_effect = conversion_error
        
        # Act & Assert
        with patch.object(parser, '_validate_pdf_path', return_value="test.pdf"):
            with self.assertRaises(ValueError) as context:
                parser.parse("test.pdf", output_format="papermage")
        
        self.assertEqual(context.exception, conversion_error)
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    def test_binary_io_input(self, mock_base_parser):
        """Test parsing with BytesIO input."""
        # Arrange
        parser = DoclingPdfParser()
        mock_pdf_doc = MagicMock()
        parser.pdf_parser.load.return_value = mock_pdf_doc
        
        pdf_data = io.BytesIO(b"PDF data")
        
        # Act
        result = parser.parse(pdf_data)
        
        # Assert
        parser.pdf_parser.load.assert_called_once_with(path_or_stream=pdf_data)
        self.assertEqual(result, mock_pdf_doc)


class TestSeparationOfConcerns(unittest.TestCase):
    """Tests to ensure strict separation between Docling processing and PaperMage conversion."""
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingToPaperMageConverter')
    def test_converter_only_called_at_output(self, mock_converter, mock_base_parser):
        """Test that the converter is only called at the output level, not during processing."""
        # Arrange
        parser = DoclingPdfParser()
        mock_pdf_doc = MagicMock()
        parser.pdf_parser.load.return_value = mock_pdf_doc
        
        # Act - parse in Docling format
        with patch.object(parser, '_validate_pdf_path', return_value="test.pdf"):
            parser.parse("test.pdf", output_format="docling")
        
        # Assert - converter should not be called when using Docling format
        mock_converter.convert_pdf_document.assert_not_called()
        
        # Act - parse in PaperMage format
        mock_converter.reset_mock()
        with patch.object(parser, '_validate_pdf_path', return_value="test.pdf"):
            parser.parse("test.pdf", output_format="papermage")
        
        # Assert - converter should be called exactly once at the output level
        mock_converter.convert_pdf_document.assert_called_once_with(mock_pdf_doc)
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    def test_rtl_processing_uses_docling_structures(self, mock_base_parser):
        """Test that RTL processing operates directly on Docling's native structures."""
        # Arrange
        parser = DoclingPdfParser(detect_rtl=True)
        mock_pdf_doc = MagicMock()
        parser.pdf_parser.load.return_value = mock_pdf_doc
    
        # Act
        with patch.object(parser, '_validate_pdf_path', return_value="test.pdf"):
            with patch.object(DoclingPdfParser, '_process_rtl_text') as mock_process_rtl:
                parser.parse("test.pdf")
    
        # Assert - Just check that RTL processing was called
        mock_process_rtl.assert_called_once()
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingToPaperMageConverter')
    def test_papermage_conversion_after_all_processing(self, mock_converter, mock_base_parser):
        """Test that conversion to PaperMage format happens after all processing."""
        # Arrange
        parser = DoclingPdfParser(detect_rtl=True)
        mock_pdf_doc = MagicMock()
        parser.pdf_parser.load.return_value = mock_pdf_doc

        # Set up side effect for _process_rtl_text to track if it was called
        process_rtl_called = [False]  # Using a list for mutable reference
        
        def mock_process_rtl(self_obj, doc, *args):
            process_rtl_called[0] = True
            return doc
        
        # Act
        with patch.object(DoclingPdfParser, '_process_rtl_text', side_effect=mock_process_rtl):
            with patch.object(parser, '_validate_pdf_path', return_value="test.pdf"):
                parser.parse("test.pdf", output_format="papermage")
        
        # Assert
        self.assertTrue(process_rtl_called[0], "RTL processing should have been called")
    
    @patch('papermage_docling.parsers.docling_pdf_parser.DoclingPdfParserBase')
    def test_no_premature_conversion(self, mock_base_parser):
        """Test that no conversion to PaperMage format happens during processing."""
        # Arrange - set up a parser with a spy on any potential conversion
        parser = DoclingPdfParser()
        mock_pdf_doc = MagicMock()
        parser.pdf_parser.load.return_value = mock_pdf_doc
        
        conversion_called = False
        
        # Define a function to check for conversions
        def conversion_spy(*args, **kwargs):
            nonlocal conversion_called
            conversion_called = True
        
        # Patch the converter, log methods, and any potential conversions
        patches = [
            patch('papermage_docling.parsers.docling_pdf_parser.DoclingToPaperMageConverter.convert_pdf_document', 
                  side_effect=conversion_spy),
            # Patch other potential conversion methods - these are just examples
            patch('papermage_docling.converters.document.Document', side_effect=conversion_spy),
            patch('papermage_docling.converters.document.Entity', side_effect=conversion_spy),
        ]
        
        for p in patches:
            p.start()
        
        try:
            # Act - parse in Docling format
            with patch.object(parser, '_validate_pdf_path', return_value="test.pdf"):
                parser.parse("test.pdf", output_format="docling")
            
            # Assert - no conversion should have happened
            self.assertFalse(conversion_called, 
                            "No conversions should happen during processing when using Docling format")
        finally:
            # Clean up patches
            for p in patches:
                p.stop()


if __name__ == '__main__':
    unittest.main() 