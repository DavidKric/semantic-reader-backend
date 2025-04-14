"""
Tests for the DocumentConversionMap class.

This module tests the DocumentConversionMap class to ensure it correctly
identifies and analyzes document format conversion points in the codebase.
"""

import os
import sys
import unittest
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from papermage_docling.analysis.document_conversion_map import (
    DocumentConversionMap,
    ConversionPoint,
    create_conversion_map
)


class TestDocumentConversionMap(unittest.TestCase):
    """Test cases for the DocumentConversionMap class."""
    
    def setUp(self):
        """Set up the test environment."""
        self.project_root = project_root
        self.converter_map = DocumentConversionMap(str(self.project_root))
        self.converter_map.analyze_codebase()
    
    def test_conversion_points_identified(self):
        """Test that conversion points are identified in the codebase."""
        # Verify we found some conversion points
        self.assertGreater(len(self.converter_map.conversion_points), 0)
        
        # Verify the DoclingPdfParser.parse conversion point was identified
        parse_points = [
            cp for cp in self.converter_map.conversion_points 
            if cp.module == "papermage_docling/parsers/docling_pdf_parser.py" and cp.function == "parse"
        ]
        self.assertEqual(len(parse_points), 1)
        
        # Verify converter methods were identified
        converter_points = [
            cp for cp in self.converter_map.conversion_points 
            if cp.module == "papermage_docling/converters/docling_to_papermage_converter.py"
        ]
        self.assertGreaterEqual(len(converter_points), 2)
    
    def test_conversion_point_attributes(self):
        """Test that ConversionPoint attributes are set correctly."""
        # Create a test conversion point
        cp = ConversionPoint(
            module="test_module.py",
            function="test_function",
            from_format="TestInput",
            to_format="TestOutput",
            description="Test description",
            impact="high",
            recommendation="Test recommendation"
        )
        
        # Verify attributes
        self.assertEqual(cp.module, "test_module.py")
        self.assertEqual(cp.function, "test_function")
        self.assertEqual(cp.from_format, "TestInput")
        self.assertEqual(cp.to_format, "TestOutput")
        self.assertEqual(cp.description, "Test description")
        self.assertEqual(cp.impact, "high")
        self.assertEqual(cp.recommendation, "Test recommendation")
        
        # Verify to_dict method
        cp_dict = cp.to_dict()
        self.assertEqual(cp_dict["module"], "test_module.py")
        self.assertEqual(cp_dict["function"], "test_function")
        self.assertEqual(cp_dict["from_format"], "TestInput")
        self.assertEqual(cp_dict["to_format"], "TestOutput")
        self.assertEqual(cp_dict["description"], "Test description")
        self.assertEqual(cp_dict["impact"], "high")
        self.assertEqual(cp_dict["recommendation"], "Test recommendation")
    
    def test_report_generation(self):
        """Test report generation."""
        # Generate report
        report = self.converter_map.generate_report()
        
        # Verify report structure
        self.assertIn("conversion_points", report)
        self.assertIn("data_flow", report)
        self.assertIn("metadata_mapping", report)
        self.assertIn("entity_layer_mapping", report)
        self.assertIn("recommendations", report)
        self.assertIn("conversion_strategy", report)
        
        # Verify recommendations are organized by impact
        self.assertIn("high", report["recommendations"])
        self.assertIn("medium", report["recommendations"])
        self.assertIn("low", report["recommendations"])
    
    def test_data_flow_diagram(self):
        """Test data flow diagram generation."""
        # Generate data flow diagram
        diagram = self.converter_map.get_data_flow_diagram()
        
        # Verify diagram structure
        self.assertIn("modules", diagram)
        self.assertIn("connections", diagram)
        
        # Verify modules and connections
        self.assertGreater(len(diagram["modules"]), 0)
        self.assertGreater(len(diagram["connections"]), 0)
    
    def test_create_conversion_map_function(self):
        """Test the create_conversion_map function."""
        # Generate report without saving to file
        report = create_conversion_map(str(self.project_root))
        
        # Verify report structure
        self.assertIn("conversion_points", report)
        self.assertIn("data_flow", report)
        self.assertIn("metadata_mapping", report)
        self.assertIn("entity_layer_mapping", report)
        self.assertIn("recommendations", report)
        self.assertIn("conversion_strategy", report)


if __name__ == "__main__":
    unittest.main() 