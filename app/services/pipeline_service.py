"""
Pipeline service for document processing operations.

This service provides simplified utilities for document processing configuration.
After the Docling refactoring, most pipeline functionality is now directly handled by Docling's document converter.
"""

import logging
from typing import Dict, List, Any, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.base import BaseModel
from app.services.base import BaseService

# Import papermage_docling components
try:
    from papermage_docling.converter import convert_document
    DOCLING_AVAILABLE = True
except ImportError:
    logging.warning("papermage_docling not available. Pipeline features will be disabled.")
    DOCLING_AVAILABLE = False

logger = logging.getLogger(__name__)


class PipelineService(BaseService):
    """
    Service for managing document processing configurations.
    
    This is a simplified version after Docling refactoring. Most pipeline functionality
    is now directly handled by Docling's document converter with appropriate configuration
    passed as options.
    """
    
    def __init__(self, db: Optional[Session] = None):
        """
        Initialize the pipeline service.
        
        Args:
            db: Optional database session
        """
        if db:
            # Initialize base service with a placeholder model
            super().__init__(BaseModel, db)
        
        if not DOCLING_AVAILABLE:
            logger.warning("Pipeline service initialized without docling support.")
            return
            
        try:
            # Initialize service with default configuration
            self._config = {
                "ocr_enabled": settings.OCR_ENABLED,
                "ocr_language": settings.OCR_LANGUAGE,
                "detect_rtl": settings.DETECT_RTL,
                "detect_tables": True,
                "detect_figures": True,
            }
            
            logger.info("Initialized pipeline service with Docling support.")
        except Exception as e:
            logger.error(f"Failed to initialize pipeline service: {e}")
            raise
    
    def get_available_features(self) -> List[str]:
        """
        Get available document processing features.
        
        Returns:
            List of available feature names
        """
        if not DOCLING_AVAILABLE:
            raise ValueError("Pipeline features are not available (docling not installed)")
        
        return ["tables", "figures", "rtl", "ocr", "metadata"]
    
    def get_pipeline_config(self) -> Dict[str, Any]:
        """
        Get document processing configuration.
        
        Returns:
            Document processing configuration dictionary
        """
        if not DOCLING_AVAILABLE:
            raise ValueError("Pipeline features are not available (docling not installed)")
        
        # Return current configuration
        return {
            "settings": self._config,
            "features": self.get_available_features(),
            "docling_version": "doclingparse_v4"  # Using Docling Parse v4 as specified
        }
    
    def update_pipeline_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update document processing configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Updated document processing configuration
        """
        if not DOCLING_AVAILABLE:
            raise ValueError("Pipeline features are not available (docling not installed)")
        
        # Update configuration
        if "settings" in config:
            settings_config = config["settings"]
            
            # Update settings
            for key in ["ocr_enabled", "ocr_language", "detect_rtl", "detect_tables", "detect_figures"]:
                if key in settings_config:
                    self._config[key] = settings_config[key]
                    
                    # Also update app settings if applicable
                    if hasattr(settings, key.upper()):
                        setattr(settings, key.upper(), settings_config[key])
        
        return self.get_pipeline_config()
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Get pipeline statistics.
        
        Returns:
            Dictionary with pipeline statistics
        """
        if not DOCLING_AVAILABLE:
            raise ValueError("Pipeline service is not available (docling not installed)")
        
        # Simplified stats as we no longer maintain a separate pipeline
        return {
            "status": "active",
            "converter": "docling.document_converter.DocumentConverter",
            "parser": "doclingparse_v4",
            "features_enabled": [
                feature for feature, enabled in {
                    "ocr": self._config.get("ocr_enabled", False),
                    "rtl": self._config.get("detect_rtl", True),
                    "tables": self._config.get("detect_tables", True),
                    "figures": self._config.get("detect_figures", True)
                }.items() if enabled
            ]
        }
    
    def get_converter_options(self) -> Dict[str, Any]:
        """
        Get options for the Docling document converter.
        
        Returns:
            Dictionary with converter options
        """
        return {
            "enable_ocr": self._config.get("ocr_enabled", False),
            "ocr_language": self._config.get("ocr_language", "eng"),
            "detect_rtl": self._config.get("detect_rtl", True),
            "detect_tables": self._config.get("detect_tables", True),
            "detect_figures": self._config.get("detect_figures", True)
        }
    
    def process_document(self, document_path: str) -> Dict[str, Any]:
        """
        Process a document using the current configuration.
        
        Args:
            document_path: Path to the document
            
        Returns:
            Processed document data
        """
        if not DOCLING_AVAILABLE:
            raise ValueError("Pipeline service is not available (docling not installed)")
        
        # Get current options
        options = self.get_converter_options()
        
        # Process the document using the converter
        return convert_document(document_path, options=options) 