"""
Report service module for managing document report generation.
"""
import logging
import os
from typing import Any, Dict, List

from fastapi import FastAPI

from app.core.config import settings
from app.reporting.html_generator import HTMLReportGenerator

logger = logging.getLogger(__name__)

class ReportService:
    """
    Service class for managing document reports.
    """
    def __init__(self, output_dir: str = None):
        """Initialize the report service."""
        self.output_dir = output_dir or settings.REPORT_OUTPUT_DIR
        self.html_generator = HTMLReportGenerator(output_dir=self.output_dir)
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"Report service initialized with output directory: {self.output_dir}")
    
    def generate_report(
        self, 
        documents: List[Dict[str, Any]], 
        include_tables: bool = True, 
        include_figures: bool = True,
        standalone: bool = False
    ) -> str:
        """
        Generate an HTML report for the specified documents.
        
        Args:
            documents: List of document dictionaries
            include_tables: Whether to include tables in the report
            include_figures: Whether to include figures in the report
            standalone: Whether the report is a standalone report
            
        Returns:
            The generated HTML content
        """
        return self.html_generator.generate_report(
            documents=documents,
            include_tables=include_tables,
            include_figures=include_figures,
            standalone=standalone
        )
    
    def save_report(self, content: str, report_id: str) -> str:
        """
        Save report content to a file.
        
        Args:
            content: HTML content to save
            report_id: ID for the report
            
        Returns:
            The path to the saved report
        """
        output_path = os.path.join(self.output_dir, f"{report_id}.html")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        logger.info(f"Report saved to {output_path}")
        return output_path

def get_report_service() -> ReportService:
    """
    Dependency function to get the report service instance.
    
    Returns:
        A new ReportService instance
    """
    return ReportService()

def init_reporting(app: FastAPI):
    """
    Initialize the reporting module and routes.
    
    Args:
        app: The FastAPI application instance
    """
    from app.reporting.routes import router
    
    # Include the reporting router
    app.include_router(router, prefix="/api", tags=["reports"])
    
    # Create output directory if it doesn't exist
    os.makedirs(settings.REPORT_OUTPUT_DIR, exist_ok=True)
    
    logger.info("Report module initialized") 