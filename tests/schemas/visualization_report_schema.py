"""
Schema definitions for document visualization reports.

This module defines schemas for generating visualization reports,
including structures for page-level visualizations, entity counts,
and overall report data.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class PageVisualization:
    """Structure representing a single page visualization."""
    number: int
    original: Optional[str] = None  # Path to original page image
    char: Optional[str] = None      # Path to character level visualization
    word: Optional[str] = None      # Path to word level visualization
    line: Optional[str] = None      # Path to line level visualization
    entity_preview: Optional[str] = None  # JSON or text preview of entities on page


@dataclass
class VisualizationReport:
    """Structure representing a complete document visualization report."""
    document_name: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    page_count: int = 0
    entity_counts: Dict[str, int] = field(default_factory=dict)
    pages: List[PageVisualization] = field(default_factory=list)
    json_structure: str = ""  # JSON structure preview
    output_path: Optional[str] = None  # Where the report will be saved

    def to_template_vars(self) -> Dict[str, Any]:
        """Convert the report to template variables for rendering."""
        return {
            "document_name": self.document_name,
            "timestamp": self.timestamp,
            "page_count": self.page_count,
            "entity_counts": self.entity_counts,
            "pages": self.pages,
            "json_structure": self.json_structure
        }


def get_entity_counts(doc_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Extract entity counts from a document.
    
    Args:
        doc_data: Document data structure
    
    Returns:
        Dictionary mapping entity types to counts
    """
    entity_counts = {}
    
    # Get counts from entities section
    if "entities" in doc_data:
        for entity_type, entities in doc_data["entities"].items():
            if isinstance(entities, list):
                entity_counts[entity_type] = len(entities)
    
    # Count pages
    if "pages" in doc_data and isinstance(doc_data["pages"], list):
        entity_counts["pages"] = len(doc_data["pages"])
        
        # Count words in pages if they exist
        word_count = 0
        for page in doc_data["pages"]:
            if "words" in page and isinstance(page["words"], list):
                word_count += len(page["words"])
        
        if word_count > 0:
            entity_counts["words_in_pages"] = word_count
    
    return entity_counts


def format_json_preview(doc_data: Dict[str, Any], max_length: int = 2000) -> str:
    """
    Format a JSON preview of the document structure.
    
    Args:
        doc_data: Document data structure
        max_length: Maximum length of the preview
    
    Returns:
        Formatted JSON preview string
    """
    import json
    
    # Get a formatted JSON string
    formatted_json = json.dumps(doc_data, indent=2)
    
    # Truncate if too long
    if len(formatted_json) > max_length:
        # Find the last complete line before max_length
        last_newline = formatted_json.rfind('\n', 0, max_length)
        if last_newline == -1:
            # If no newline found, just truncate
            truncated = formatted_json[:max_length]
        else:
            truncated = formatted_json[:last_newline]
        
        return truncated + "\n...\n(truncated)"
    
    return formatted_json 