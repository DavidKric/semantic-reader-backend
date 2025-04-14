"""
API Module for Document Format Conversion.

This module provides an extensible framework for converting between different document formats
at API boundaries, implementing the Gateway and Adapter patterns. The gateway serves as a
unified entry point for document operations, while adapters handle the conversion
between different formats.

Key components:
- DocumentGateway: Main interface for document operations
- BaseAdapter: Abstract base class for all format adapters
- FormatVersionInfo: Helper class to store format version information
- AdapterRegistry: Factory class for registering and retrieving adapters
"""

from typing import Dict, List, Any, Optional, Union, Type

# Legacy API components (for backward compatibility)
from .base import BaseAdapter, FormatVersionInfo, AdapterRegistry
from .papermage import (
    PaperMageAdapter, 
    PaperMageV1Adapter, 
    PaperMageLatestAdapter
)

# New Gateway interface
from .gateway import DocumentGateway, gateway

__all__ = [
    # New Gateway API (preferred)
    'DocumentGateway',
    'gateway',
    
    # Legacy API components (for backward compatibility)
    'BaseAdapter',
    'FormatVersionInfo',
    'AdapterRegistry',
    'PaperMageAdapter',
    'PaperMageV1Adapter',
    'PaperMageLatestAdapter',
    'get_adapter',
    'get_adapter_registry'
]

# Default adapter registry instance
_adapter_registry = None


def get_adapter_registry() -> AdapterRegistry:
    """
    Get or create the default adapter registry.
    
    Returns:
        AdapterRegistry: The global adapter registry instance
    """
    global _adapter_registry
    if _adapter_registry is None:
        _adapter_registry = AdapterRegistry()
        # Register default adapters
        from .papermage import register_default_adapters
        register_default_adapters(_adapter_registry)
    return _adapter_registry


def get_adapter(
    source_format: str,
    target_format: str,
    source_version: Optional[str] = None,
    target_version: Optional[str] = None
) -> BaseAdapter:
    """
    Get an appropriate adapter for converting between formats.
    
    Note: This function is maintained for backward compatibility.
    New code should use the DocumentGateway interface.
    
    Args:
        source_format: Format of the source document
        target_format: Format of the target document
        source_version: Version of the source format (optional)
        target_version: Version of the target format (optional)
        
    Returns:
        BaseAdapter: An adapter instance for the requested conversion
        
    Raises:
        ValueError: If no suitable adapter is found
    """
    registry = get_adapter_registry()
    return registry.get_adapter(
        source_format, 
        target_format,
        source_version,
        target_version
    )