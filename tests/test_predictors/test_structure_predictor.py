"""
Tests for the structure predictor module.
"""

import unittest
from unittest.mock import patch, MagicMock
import io

from papermage_docling.predictors.structure_predictor import (
    StructurePredictor, get_structure_predictor
)


class TestStructurePredictor(unittest.TestCase):
    """Tests for the StructurePredictor class."""
    
    def test_initialization(self):
        """Test basic initialization of StructurePredictor."""
        predictor = StructurePredictor(
            enable_layout_analysis=True,
            enable_table_detection=False,
            layout_confidence_threshold=0.7
        )
        
        self.assertTrue(predictor.enable_layout_analysis)
        self.assertFalse(predictor.enable_table_detection)
        self.assertEqual(predictor.layout_confidence_threshold, 0.7)
    
    def test_singleton(self):
        """Test singleton pattern for structure predictor."""
        predictor1 = get_structure_predictor()
        predictor2 = get_structure_predictor()
        
        # Should be the same instance
        self.assertIs(predictor1, predictor2)
    
    @patch('papermage_docling.predictors.structure_predictor.HAS_DOCLING_MODELS', False)
    def test_manual_processing(self):
        """Test manual fallback processing when docling models aren't available."""
        predictor = StructurePredictor()
        
        # Create mock document
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_line1 = MagicMock(text="Document Title")
        mock_line2 = MagicMock(text="")  # Empty line
        mock_line3 = MagicMock(text="This is a paragraph with some content.")
        mock_line4 = MagicMock(text="This is the continuation of the paragraph.")
        mock_line5 = MagicMock(text="1. Introduction")  # Section heading
        mock_page.lines = [mock_line1, mock_line2, mock_line3, mock_line4, mock_line5]
        mock_doc.pages = [mock_page]
        mock_doc.metadata = {}
        
        # Apply structure prediction
        predictor.apply(mock_doc)
        
        # Verify document was processed
        self.assertTrue(mock_doc.metadata.get('structure_analyzed', False))
        
        # Verify page metadata was updated
        self.assertTrue(mock_page.metadata.get('has_title', False))
        self.assertTrue(mock_page.metadata.get('has_paragraphs', False))
        self.assertTrue(mock_page.metadata.get('has_headings', False))
    
    def test_extract_titles(self):
        """Test title extraction from page."""
        predictor = StructurePredictor()
        
        # Create mock page with title
        mock_page = MagicMock()
        mock_page.lines = [
            MagicMock(text="Document Title"),  # Title
            MagicMock(text="Subtitle"),  # Subtitle
            MagicMock(text=""),  # Empty line
            MagicMock(text="This is a paragraph with some content.")  # Content
        ]
        
        titles = predictor._extract_titles(mock_page)
        
        # Should find two titles
        self.assertEqual(len(titles), 2)
        self.assertEqual(titles[0]['text'], "Document Title")
        self.assertEqual(titles[0]['type'], "main_title")
        self.assertEqual(titles[1]['text'], "Subtitle")
        self.assertEqual(titles[1]['type'], "subtitle")
    
    def test_extract_paragraphs(self):
        """Test paragraph extraction from page."""
        predictor = StructurePredictor()
        
        # Create mock page with paragraphs
        mock_page = MagicMock()
        mock_page.lines = [
            MagicMock(text="Document Title"),  # Title
            MagicMock(text=""),  # Empty line
            MagicMock(text="This is paragraph 1, line 1."),  # Paragraph 1, line 1
            MagicMock(text="This is paragraph 1, line 2."),  # Paragraph 1, line 2
            MagicMock(text=""),  # Empty line
            MagicMock(text="This is paragraph 2."),  # Paragraph 2
        ]
        
        paragraphs = predictor._extract_paragraphs(mock_page)
        
        # Should find two paragraphs
        self.assertEqual(len(paragraphs), 2)
        self.assertIn("This is paragraph 1, line 1.", paragraphs[0]['text'])
        self.assertIn("This is paragraph 1, line 2.", paragraphs[0]['text'])
        self.assertEqual(paragraphs[1]['text'], "This is paragraph 2.")
    
    def test_extract_headings(self):
        """Test heading extraction from page."""
        predictor = StructurePredictor()
        
        # Create mock page with headings
        mock_page = MagicMock()
        mock_page.lines = [
            MagicMock(text="Document Title"),  # Title
            MagicMock(text=""),  # Empty line
            MagicMock(text="Abstract"),  # Level 1 heading
            MagicMock(text="This is the abstract."),  # Content
            MagicMock(text=""),  # Empty line
            MagicMock(text="1. Introduction"),  # Level 1 heading
            MagicMock(text="This is the introduction."),  # Content
            MagicMock(text=""),  # Empty line
            MagicMock(text="2.1 Background"),  # Level 2 heading
        ]
        
        headings = predictor._extract_headings(mock_page)
        
        # Should find three headings
        self.assertEqual(len(headings), 3)
        self.assertEqual(headings[0]['text'], "Abstract")
        self.assertEqual(headings[0]['level'], 1)
        self.assertEqual(headings[1]['text'], "1. Introduction")
        self.assertEqual(headings[1]['level'], 1)
    
    def test_extract_tables(self):
        """Test table extraction from page."""
        predictor = StructurePredictor()
        
        # Create mock page with table-like content
        mock_page = MagicMock()
        mock_page.lines = [
            MagicMock(text="Document Title"),  # Title
            MagicMock(text=""),  # Empty line
            MagicMock(text="Table 1: Sample Data"),  # Table title
            MagicMock(text=""),  # Empty line
            MagicMock(text="Name    Age    Location"),  # Table header
            MagicMock(text="John    25     New York"),  # Table row 1
            MagicMock(text="Jane    30     Boston"),  # Table row 2
            MagicMock(text="Bob     22     Chicago"),  # Table row 3
            MagicMock(text=""),  # Empty line
            MagicMock(text="End of table."),  # Content
        ]
        
        tables = predictor._extract_tables(mock_page)
        
        # Should find one table
        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0]['start_line'], 4)  # Table header
        self.assertEqual(tables[0]['end_line'], 7)  # Last table row
        self.assertEqual(tables[0]['num_rows'], 4)  # 4 rows (header + 3 data rows)
    
    @patch('papermage_docling.predictors.structure_predictor.Pipeline')
    @patch('papermage_docling.predictors.structure_predictor.HAS_DOCLING_MODELS', True)
    def test_docling_pipeline(self, mock_pipeline_class):
        """Test processing with docling pipeline when available."""
        # Setup mock pipeline
        mock_pipeline = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline
        
        predictor = StructurePredictor()
        
        # Create mock document
        mock_doc = MagicMock()
        mock_doc.pages = [MagicMock()]
        
        # Apply structure prediction
        predictor.apply(mock_doc)
        
        # Verify docling pipeline was used
        mock_pipeline.process.assert_called_once()


class TestStructurePredictorIntegration(unittest.TestCase):
    """Integration tests for StructurePredictor."""
    
    @patch('papermage_docling.predictors.structure_predictor.DoclingDocument')
    @patch('papermage_docling.predictors.structure_predictor.PdfDocument')
    def test_end_to_end_basic(self, mock_pdf_doc_class, mock_docling_doc_class):
        """Test basic end-to-end structure prediction."""
        # This test simulates the document processing flow without requiring
        # actual docling models or documents
        
        # Create a predictor with default settings
        predictor = StructurePredictor(
            enable_layout_analysis=True,
            enable_table_detection=True,
            enable_heading_detection=True
        )
        
        # Create a mock document with sample content
        mock_pdf_doc = MagicMock()
        mock_page = MagicMock()
        
        # Create lines simulating a document with title, headings, paragraphs, and a table
        mock_lines = [
            MagicMock(text="Document Title"),  # Title
            MagicMock(text=""),  # Empty line
            MagicMock(text="Abstract"),  # Section heading
            MagicMock(text="This is an abstract. It summarizes the document."),  # Paragraph
            MagicMock(text=""),  # Empty line
            MagicMock(text="1. Introduction"),  # Section heading
            MagicMock(text="This is the introduction to the document."),  # Paragraph
            MagicMock(text="It continues with more information."),  # Paragraph cont.
            MagicMock(text=""),  # Empty line
            MagicMock(text="Table 1: Results"),  # Table title
            MagicMock(text="Method    Accuracy    Time"),  # Table header
            MagicMock(text="A         95%         10s"),  # Table row
            MagicMock(text="B         92%         8s"),  # Table row
        ]
        
        mock_page.lines = mock_lines
        mock_pdf_doc.pages = [mock_page]
        mock_pdf_doc.metadata = {}
        
        # Apply structure prediction
        predictor.apply(mock_pdf_doc)
        
        # Check that document was processed and metadata was created
        self.assertTrue(mock_pdf_doc.metadata.get('structure_analyzed', False))
        
        # Check that page metadata was updated with structure information
        self.assertTrue(mock_page.metadata.get('has_title', False))
        self.assertTrue(mock_page.metadata.get('has_paragraphs', False))
        self.assertTrue(mock_page.metadata.get('has_headings', False))
        self.assertTrue(mock_page.metadata.get('has_tables', False))
        
        # Verify structure elements were detected in expected quantities
        structure_elements = mock_page.metadata.get('structure_elements', {})
        self.assertGreaterEqual(structure_elements.get('titles', 0), 1)  # At least 1 title
        self.assertGreaterEqual(structure_elements.get('paragraphs', 0), 1)  # At least 1 paragraph
        self.assertGreaterEqual(structure_elements.get('headings', 0), 2)  # At least 2 headings
        self.assertGreaterEqual(structure_elements.get('tables', 0), 1)  # At least 1 table


if __name__ == '__main__':
    unittest.main() 