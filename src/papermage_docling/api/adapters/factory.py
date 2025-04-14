"""
Adapter factory for creating document format adapters.

This module provides factory functions for creating adapters to convert
between different document formats supported by the semantic reader.
"""

from typing import Any, Dict, List, Optional, Type, Union

from papermage_docling.api.adapters.base import BaseAdapter, AdapterRegistry, FormatVersionInfo
from papermage_docling.api.adapters.pdf import PdfToPapermageAdapter

# Initialize the global adapter registry
_adapter_registry = AdapterRegistry()

# Register built-in adapters
_adapter_registry.register_adapter(PdfToPapermageAdapter)


def get_adapter(
    source_format: Union[str, FormatVersionInfo],
    target_format: Union[str, FormatVersionInfo],
    **adapter_kwargs
) -> BaseAdapter:
    """
    Get an appropriate adapter for converting between the specified formats.
    
    Args:
        source_format: Source format to convert from (string or FormatVersionInfo)
        target_format: Target format to convert to (string or FormatVersionInfo)
        **adapter_kwargs: Additional parameters to pass to the adapter constructor
        
    Returns:
        BaseAdapter: An instance of the appropriate adapter
        
    Raises:
        ValueError: If no compatible adapter is found or formats are invalid
    """
    # Convert string formats to FormatVersionInfo objects
    if isinstance(source_format, str):
        source_format = FormatVersionInfo(source_format)
    if isinstance(target_format, str):
        target_format = FormatVersionInfo(target_format)
        
    # Get an appropriate adapter class from the registry
    adapter_class = _adapter_registry.get_adapter_for_formats(
        source_format, target_format
    )
    
    if not adapter_class:
        raise ValueError(
            f"No adapter found for converting from {source_format} to {target_format}"
        )
    
    # Create and return an instance of the adapter
    return adapter_class(**adapter_kwargs)


def register_adapter(adapter_class: Type[BaseAdapter]) -> None:
    """
    Register a custom adapter with the global adapter registry.
    
    Args:
        adapter_class: The adapter class to register
    """
    _adapter_registry.register_adapter(adapter_class)


def list_supported_formats() -> Dict[str, List[str]]:
    """
    List all supported format conversions.
    
    Returns:
        Dict[str, List[str]]: A dictionary mapping source formats to 
        lists of supported target formats
    """
    result = {}
    
    for adapter_class in _adapter_registry.get_all_adapters():
        # Create a temporary instance to get format info
        adapter = adapter_class()
        source = str(adapter.source_format)
        target = str(adapter.target_format)
        
        if source not in result:
            result[source] = []
            
        if target not in result[source]:
            result[source].append(target)
            
    return result


def convert_document(
    document: Any,
    source_format: Union[str, FormatVersionInfo],
    target_format: Union[str, FormatVersionInfo],
    **kwargs
) -> Any:
    """
    Convert a document from one format to another.
    
    This is a convenience function that gets the appropriate adapter
    and uses it to convert the document.
    
    Args:
        document: The document to convert
        source_format: Source format to convert from
        target_format: Target format to convert to
        **kwargs: Additional parameters for the adapter and conversion
        
    Returns:
        Any: The converted document
        
    Raises:
        ValueError: If no compatible adapter is found
    """
    # Extract adapter-specific kwargs (prefixed with adapter_)
    adapter_kwargs = {}
    conversion_kwargs = {}
    
    for key, value in kwargs.items():
        if key.startswith("adapter_"):
            adapter_kwargs[key[8:]] = value
        else:
            conversion_kwargs[key] = value
    
    # Get the appropriate adapter
    adapter = get_adapter(source_format, target_format, **adapter_kwargs)
    
    # Convert the document
    return adapter.convert(document, **conversion_kwargs) 