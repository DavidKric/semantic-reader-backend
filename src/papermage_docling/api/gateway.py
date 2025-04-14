"""
Document Gateway for the Semantic Reader API.

This module provides the gateway interface for document operations in the semantic reader,
encapsulating the underlying adapter mechanism and providing a unified entry point.
"""

from typing import Any, Dict, List, Optional, Type, Union

from papermage_docling.api.adapters.base import BaseAdapter, FormatVersionInfo
from papermage_docling.api.adapters.factory import (
    get_adapter,
    register_adapter,
    list_supported_formats,
    convert_document as _convert_document
)


class DocumentGateway:
    """
    Gateway for document operations in the semantic reader.
    
    This class provides a unified interface for working with documents
    across different formats, encapsulating the underlying adapter mechanism
    and providing a clean API for the rest of the application.
    """
    
    @staticmethod
    def convert(
        document: Any,
        source_format: Union[str, FormatVersionInfo],
        target_format: Union[str, FormatVersionInfo],
        **kwargs
    ) -> Any:
        """
        Convert a document from one format to another.
        
        Args:
            document: The document to convert (path, bytes, or file-like object)
            source_format: Format to convert from (string or FormatVersionInfo)
            target_format: Format to convert to (string or FormatVersionInfo)
            **kwargs: Additional parameters for the conversion process
                - Parameters starting with "adapter_" are passed to the adapter constructor
                - Other parameters are passed to the conversion method
                
        Returns:
            Any: The converted document
            
        Raises:
            ValueError: If no compatible adapter is found or conversion fails
        """
        return _convert_document(document, source_format, target_format, **kwargs)
    
    @staticmethod
    def supported_formats() -> Dict[str, List[str]]:
        """
        Get a list of all supported format conversions.
        
        Returns:
            Dict[str, List[str]]: A dictionary mapping source formats to 
            lists of supported target formats
        """
        return list_supported_formats()
    
    @staticmethod
    def register_format_adapter(adapter_class: Type[BaseAdapter]) -> None:
        """
        Register a custom document format adapter.
        
        Args:
            adapter_class: The adapter class to register
            
        Raises:
            TypeError: If adapter_class is not a subclass of BaseAdapter
        """
        register_adapter(adapter_class)


# Create a singleton instance for easy access
gateway = DocumentGateway() 