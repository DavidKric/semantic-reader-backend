"""
Utility module for generating visualization reports using an HTML template.
"""
import os
import json
import logging
import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

class VisualizationReportGenerator:
    """Generate HTML reports for document visualizations."""
    
    def __init__(self, template_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the generator with a template directory.
        
        Args:
            template_dir: Path to the directory containing the templates.
                If None, will try to use the default template at 'tests/templates'.
        """
        if template_dir is None:
            # Try to find the default template directory
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent.parent
            template_dir = project_root / "tests" / "templates"
            
            if not template_dir.exists():
                logger.warning(f"Default template directory not found at {template_dir}")
                # Fallback to the directory of this file
                template_dir = current_file.parent / "templates"
                
                if not template_dir.exists():
                    template_dir.mkdir(parents=True, exist_ok=True)
                    logger.warning(f"Created template directory at {template_dir}")
        
        self.template_dir = Path(template_dir)
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
    
    def _convert_paths_to_relative(self, visualizations: Dict[str, Dict[int, str]], 
                                   output_path: Union[str, Path]) -> Dict[str, Dict[int, str]]:
        """
        Convert absolute paths in visualizations to paths relative to the output directory.
        
        Args:
            visualizations: Dictionary mapping visualization type to page number to path
            output_path: Path of the output HTML file
            
        Returns:
            Dictionary with paths converted to relative paths
        """
        output_dir = Path(output_path).parent
        result = {}
        
        for viz_type, pages in visualizations.items():
            result[viz_type] = {}
            for page_num, path in pages.items():
                if path:
                    path_obj = Path(path)
                    if path_obj.is_absolute():
                        try:
                            rel_path = path_obj.relative_to(output_dir)
                            result[viz_type][page_num] = str(rel_path)
                        except ValueError:
                            # If the path is not relative to the output directory,
                            # copy the file to the output directory
                            if path_obj.exists():
                                new_filename = path_obj.name
                                new_path = output_dir / new_filename
                                import shutil
                                shutil.copy2(path_obj, new_path)
                                result[viz_type][page_num] = str(new_path.relative_to(output_dir))
                            else:
                                result[viz_type][page_num] = path
                    else:
                        result[viz_type][page_num] = path
                else:
                    result[viz_type][page_num] = None
                    
        return result
    
    def generate_report(self, 
                        output_path: Union[str, Path], 
                        title: str, 
                        filename: str, 
                        visualizations: Dict[str, Dict[int, str]],
                        metadata: Optional[Dict[str, Any]] = None,
                        document_stats: Optional[Dict[str, Any]] = None,
                        additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate an HTML report with visualizations.
        
        Args:
            output_path: Path to save the HTML report
            title: Title of the report
            filename: Filename of the document being visualized
            visualizations: Dictionary with keys for visualization types ('original', 'char', 'word', 'line')
                           and values as dictionaries mapping page numbers to image paths
            metadata: Optional metadata to include in the report
            document_stats: Optional statistics about the document
            additional_context: Optional additional context to include in the template
            
        Returns:
            Path to the generated HTML report
        """
        output_path = Path(output_path)
        output_dir = output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get the maximum page number across all visualizations
        max_page = 0
        for viz_type, pages in visualizations.items():
            if pages and len(pages) > 0:
                max_page = max(max_page, max(pages.keys()))
        
        # Convert absolute paths to relative paths
        rel_visualizations = self._convert_paths_to_relative(visualizations, output_path)
        
        # Create context for the template
        context = {
            'title': title,
            'filename': filename,
            'processing_date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'num_pages': max_page,
            'original_pages': rel_visualizations.get('original', {}),
            'char_pages': rel_visualizations.get('char', {}),
            'word_pages': rel_visualizations.get('word', {}),
            'line_pages': rel_visualizations.get('line', {}),
            'metadata': metadata or {},
            'document_stats': document_stats or {},
        }
        
        # Add raw data if available in document_stats
        if document_stats and "raw_data" in document_stats:
            context['raw_data'] = document_stats["raw_data"]
            # Create a pretty-printed JSON preview
            try:
                context['json_preview'] = json.dumps(document_stats["raw_data"], indent=2)
            except Exception as e:
                logger.warning(f"Failed to serialize raw data to JSON: {e}")
                context['json_preview'] = "Error serializing data to JSON"
        
        # Add any additional context
        if additional_context:
            context.update(additional_context)
        
        # Render the template
        template = self.env.get_template('visualization_report.html')
        html_content = template.render(**context)
        
        # Write the HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Generated report at {output_path}")
        return str(output_path)

def generate_document_report(
    output_path: Union[str, Path], 
    title: str, 
    filename: str, 
    visualizations: Dict[str, Dict[int, str]],
    metadata: Optional[Dict[str, Any]] = None,
    document_stats: Optional[Dict[str, Any]] = None,
    template_dir: Optional[Union[str, Path]] = None,
    additional_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Convenience function to generate a document visualization report.
    
    Args:
        output_path: Path to save the HTML report
        title: Title of the report
        filename: Filename of the document being visualized
        visualizations: Dictionary with keys for visualization types ('original', 'char', 'word', 'line')
                       and values as dictionaries mapping page numbers to image paths
        metadata: Optional metadata to include in the report
        document_stats: Optional statistics about the document
        template_dir: Optional path to the template directory
        additional_context: Optional additional context to include in the template
        
    Returns:
        Path to the generated HTML report
    """
    generator = VisualizationReportGenerator(template_dir)
    return generator.generate_report(
        output_path, 
        title, 
        filename, 
        visualizations,
        metadata,
        document_stats,
        additional_context
    ) 