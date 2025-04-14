"""
Document Conversion Analysis and Map

This module analyzes the current data flow in the PaperMage-Docling codebase,
identifying all conversion points between Docling's native document structures 
and PaperMage's format. This analysis is used to guide the refactoring process 
to standardize on Docling's native document structures throughout the codebase.
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
import json
import os

logger = logging.getLogger(__name__)

# Key document classes and formats identified in the codebase
DOCLING_FORMATS = [
    "DoclingDocument",
    "PdfDocument",
    "TextItem",
    "TableItem",
    "PictureItem",
    "KeyValueItem",
    "Page",
    "TextCellUnit"
]

PAPERMAGE_FORMATS = [
    "Document", 
    "Entity", 
    "Span", 
    "Box"
]

class ConversionPoint:
    """Represents a point in the code where document format conversion occurs."""
    
    def __init__(
        self, 
        module: str, 
        function: str, 
        from_format: str, 
        to_format: str, 
        description: str,
        impact: str = "medium",
        recommendation: str = ""
    ):
        """
        Initialize a conversion point.
        
        Args:
            module: The module where conversion occurs (file path)
            function: The function or method name performing the conversion
            from_format: The source document format
            to_format: The target document format
            description: Description of the conversion
            impact: Impact of refactoring this conversion (high, medium, low)
            recommendation: Recommendation for refactoring
        """
        self.module = module
        self.function = function
        self.from_format = from_format
        self.to_format = to_format
        self.description = description
        self.impact = impact
        self.recommendation = recommendation
    
    def __repr__(self) -> str:
        return (f"ConversionPoint(module='{self.module}', function='{self.function}', "
                f"from='{self.from_format}', to='{self.to_format}')")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "module": self.module,
            "function": self.function,
            "from_format": self.from_format,
            "to_format": self.to_format,
            "description": self.description,
            "impact": self.impact,
            "recommendation": self.recommendation
        }


class DocumentConversionMap:
    """
    Analyzes and maps document format conversions in the codebase.
    
    This class identifies and documents all points where conversions between
    Docling's native document structures and PaperMage format occur, to guide
    the refactoring process for standardizing on Docling formats.
    """
    
    def __init__(self, project_root: str = None):
        """
        Initialize the conversion mapper.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root or os.getcwd()
        self.conversion_points: List[ConversionPoint] = []
        logger.info(f"Initialized DocumentConversionMap with root: {self.project_root}")
    
    def analyze_codebase(self) -> None:
        """
        Analyze the codebase to identify and document conversion points.
        
        This method populates the conversion_points list with identified conversions.
        """
        # The conversion points below are based on manual analysis of the codebase
        # In a real implementation, you would use AST parsing or other static analysis

        # 1. DoclingPdfParser.parse() conversion point
        self.conversion_points.append(
            ConversionPoint(
                module="papermage_docling/parsers/docling_pdf_parser.py",
                function="parse",
                from_format="PdfDocument",
                to_format="Document (PaperMage)",
                description="Converts Docling's PdfDocument to PaperMage Document format based on output_format parameter",
                impact="high",
                recommendation="Keep this conversion point but ensure it's only at the API boundary. Modify internal processing to work with Docling native formats only."
            )
        )
        
        # 2. DoclingToPaperMageConverter.convert_pdf_document() conversion method
        self.conversion_points.append(
            ConversionPoint(
                module="papermage_docling/converters/docling_to_papermage_converter.py",
                function="convert_pdf_document",
                from_format="PdfDocument",
                to_format="Document (PaperMage)",
                description="Dedicated method for converting Docling's PdfDocument to PaperMage format",
                impact="medium",
                recommendation="Keep this method but ensure it's only called at API boundaries, not during internal processing."
            )
        )
        
        # 3. DoclingToPaperMageConverter.convert_docling_document() conversion method
        self.conversion_points.append(
            ConversionPoint(
                module="papermage_docling/converters/docling_to_papermage_converter.py",
                function="convert_docling_document",
                from_format="DoclingDocument",
                to_format="Document (PaperMage)",
                description="Dedicated method for converting Docling's DoclingDocument to PaperMage format",
                impact="medium",
                recommendation="Keep this method but ensure it's only called at API boundaries, not during internal processing."
            )
        )
        
        # 4. Structure Predictor potential conversion
        self.conversion_points.append(
            ConversionPoint(
                module="papermage_docling/predictors/structure_predictor.py",
                function="apply",
                from_format="Union[PdfDocument, DoclingDocument]",
                to_format="Internal modifications",
                description="Structure predictor works with both PdfDocument and DoclingDocument, but should be standardized to only use DoclingDocument",
                impact="medium",
                recommendation="Update to accept only DoclingDocument and ensure no conversion to PaperMage format occurs within the predictor."
            )
        )
        
        # 5. RTL Utils conversion
        self.conversion_points.append(
            ConversionPoint(
                module="papermage_docling/predictors/rtl_utils.py",
                function="normalize_document",
                from_format="Potentially mixed formats",
                to_format="Modified document",
                description="The RTL utilities may be used with both Docling and PaperMage formats",
                impact="high",
                recommendation="Update to work exclusively with Docling's native structures, removing any PaperMage-specific handling."
            )
        )
        
        # 6. Language Predictor 
        self.conversion_points.append(
            ConversionPoint(
                module="papermage_docling/predictors/language_predictor.py",
                function="predict_document_language",
                from_format="str or Document",
                to_format="Language prediction result",
                description="Language predictor works with text or Document objects, but should be standardized",
                impact="medium",
                recommendation="Update to accept only text or DoclingDocument, removing any PaperMage-specific handling."
            )
        )
        
        # 7. Table Predictor
        self.conversion_points.append(
            ConversionPoint(
                module="papermage_docling/predictors/table_predictor.py",
                function="apply",
                from_format="Union[PdfDocument, DoclingDocument]",
                to_format="Internal modifications",
                description="Table predictor works with both PdfDocument and DoclingDocument, but should be standardized",
                impact="medium",
                recommendation="Update to accept only DoclingDocument and ensure no conversion to PaperMage format occurs within the predictor."
            )
        )
        
        # 8. Figure Predictor
        self.conversion_points.append(
            ConversionPoint(
                module="papermage_docling/predictors/figure_predictor.py",
                function="apply",
                from_format="Union[PdfDocument, DoclingDocument]",
                to_format="Internal modifications",
                description="Figure predictor works with both PdfDocument and DoclingDocument, but should be standardized",
                impact="medium",
                recommendation="Update to accept only DoclingDocument and ensure no conversion to PaperMage format occurs within the predictor."
            )
        )
        
        logger.info(f"Identified {len(self.conversion_points)} conversion points in the codebase")
    
    def get_data_flow_diagram(self) -> Dict[str, Any]:
        """
        Generate a data flow diagram showing conversion points.
        
        Returns:
            Dictionary representing the data flow diagram
        """
        modules = set()
        connections = []
        
        for cp in self.conversion_points:
            modules.add(cp.module)
            connections.append({
                "from_module": cp.module,
                "from_format": cp.from_format,
                "to_format": cp.to_format,
                "function": cp.function
            })
        
        return {
            "modules": list(modules),
            "connections": connections
        }
    
    def get_metadata_mapping(self) -> Dict[str, Dict[str, str]]:
        """
        Generate a mapping of metadata fields between formats.
        
        Returns:
            Dictionary mapping metadata fields between Docling and PaperMage formats
        """
        # This is a manual mapping based on analysis of both document formats
        return {
            "DoclingDocument to PaperMage": {
                "metadata.title": "metadata.title",
                "metadata.author": "metadata.author",
                "metadata.language": "metadata.language",
                "metadata.language_name": "metadata.language_name",
                "metadata.is_rtl_language": "metadata.is_rtl_language",
                "metadata.has_rtl_content": "metadata.has_rtl_content",
                "metadata.rtl_pages_count": "metadata.rtl_pages_count",
                "metadata.rtl_lines_count": "metadata.rtl_lines_count"
            },
            "PaperMage to DoclingDocument": {
                "metadata.title": "metadata.title",
                "metadata.author": "metadata.author",
                "metadata.language": "metadata.language",
                "metadata.is_rtl_language": "metadata.is_rtl_language",
                "metadata.has_rtl_content": "metadata.has_rtl_content"
            }
        }
    
    def get_entity_layer_mapping(self) -> Dict[str, Dict[str, str]]:
        """
        Generate a mapping of entity layers between formats.
        
        Returns:
            Dictionary mapping entity layers between Docling and PaperMage formats
        """
        # This is a manual mapping based on analysis of both document formats
        return {
            "DoclingDocument to PaperMage": {
                "text items (paragraphs)": "paragraphs layer",
                "text items (sentences)": "sentences layer",
                "text items (words)": "words/tokens layer",
                "tables": "tables layer",
                "pictures": "figures layer",
                "key-value items": "Various metadata or special entity layers"
            },
            "PaperMage to DoclingDocument": {
                "paragraphs layer": "text items (category=paragraph)",
                "sentences layer": "text items (as sentences of paragraphs)",
                "words/tokens layer": "text items (as words of paragraphs)",
                "tables layer": "tables",
                "figures layer": "pictures",
                "bibliography layer": "text items (category=reference)"
            }
        }
    
    def get_conversion_recommendations(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate recommendations for refactoring the conversion points.
        
        Returns:
            Dictionary with recommendations by impact level
        """
        recommendations = {
            "high": [],
            "medium": [],
            "low": []
        }
        
        for cp in self.conversion_points:
            recommendations[cp.impact].append({
                "module": cp.module,
                "function": cp.function,
                "recommendation": cp.recommendation
            })
        
        return recommendations
    
    def generate_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive report of the conversion analysis.
        
        Args:
            output_file: Optional file path to save the report as JSON
            
        Returns:
            Dictionary containing the full analysis report
        """
        report = {
            "conversion_points": [cp.to_dict() for cp in self.conversion_points],
            "data_flow": self.get_data_flow_diagram(),
            "metadata_mapping": self.get_metadata_mapping(),
            "entity_layer_mapping": self.get_entity_layer_mapping(),
            "recommendations": self.get_conversion_recommendations(),
            "conversion_strategy": {
                "api_boundaries": [
                    {
                        "module": "papermage_docling/parsers/docling_pdf_parser.py",
                        "function": "parse",
                        "description": "Main API entry point with output_format parameter",
                        "recommended_action": "Keep but ensure conversion only happens at the end"
                    },
                    {
                        "module": "papermage_docling/api/api_service.py",
                        "function": "process_document",
                        "description": "API endpoint for processing documents",
                        "recommended_action": "Update to convert from PaperMage format at input, process using Docling format, and convert back at output only"
                    }
                ],
                "internal_processing": [
                    {
                        "component": "Predictors (structure, table, figure, language)",
                        "recommended_action": "Update to exclusively use DoclingDocument and related structures"
                    },
                    {
                        "component": "RTL utilities",
                        "recommended_action": "Update to exclusively use DoclingDocument text structures" 
                    }
                ]
            },
            "document_structure_differences": {
                "hierarchy": {
                    "docling": "Uses a tree structure with body/furniture and nested items with parent-child references",
                    "papermage": "Uses a flat layer-based structure with entity layers like paragraphs, sentences, etc."
                },
                "entity_representation": {
                    "docling": "Different classes for different types (TextItem, TableItem, etc.) with category attributes",
                    "papermage": "Uniform Entity class with spans, boxes, and metadata to distinguish types"
                },
                "coordinate_system": {
                    "docling": "Native PDF coordinates with BBox objects",
                    "papermage": "Custom Box objects with x0, y0, x1, y1, page attributes"
                }
            }
        }
        
        if output_file:
            output_path = Path(output_file)
            os.makedirs(output_path.parent, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Saved conversion analysis report to {output_file}")
        
        return report


def create_conversion_map(project_root: str = None, output_file: str = None) -> Dict[str, Any]:
    """
    Create a document conversion map for the codebase.
    
    Args:
        project_root: Root directory of the project
        output_file: Optional file path to save the report as JSON
        
    Returns:
        Dictionary containing the analysis report
    """
    mapper = DocumentConversionMap(project_root)
    mapper.analyze_codebase()
    return mapper.generate_report(output_file)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze document format conversions in the codebase")
    parser.add_argument("--project-root", default=None, help="Root directory of the project")
    parser.add_argument("--output", default="analysis/conversion_map.json", help="Output file for the report")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    create_conversion_map(args.project_root, args.output) 