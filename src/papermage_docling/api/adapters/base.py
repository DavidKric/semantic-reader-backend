"""
Base adapter interfaces and registry for document format conversion.

This module defines the base adapter interface and registry system for
managing document format adapters in the semantic reader.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Type, TypeVar, Union


@dataclass(frozen=True)
class FormatVersionInfo:
    """Information about a document format and version."""
    
    format_name: str
    major_version: Optional[int] = None
    minor_version: Optional[int] = None
    
    def __post_init__(self):
        """Validate the format name and version information."""
        if not self.format_name:
            raise ValueError("Format name cannot be empty")
        
        # If one version component is specified, both should be
        if (self.major_version is None) != (self.minor_version is None):
            raise ValueError("Both major and minor versions must be specified together")
            
    def __str__(self) -> str:
        """String representation of the format version."""
        if self.major_version is not None and self.minor_version is not None:
            return f"{self.format_name}-v{self.major_version}.{self.minor_version}"
        return self.format_name
        
    def is_compatible_with(self, other: "FormatVersionInfo") -> bool:
        """
        Check if this format is compatible with another format.
        
        Args:
            other: The other format to check compatibility with
            
        Returns:
            bool: True if formats are compatible, False otherwise
        """
        # Different format names are never compatible
        if self.format_name != other.format_name:
            return False
            
        # If either format doesn't specify a version, they're compatible
        if self.major_version is None or other.major_version is None:
            return True
            
        # For versioned formats, major versions must match
        return self.major_version == other.major_version


# Type variable for BaseAdapter subclasses
T = TypeVar("T", bound="BaseAdapter")


class BaseAdapter(ABC):
    """
    Base class for all document format adapters.
    
    Adapters are used to convert documents between different formats
    supported by the semantic reader.
    """
    
    @property
    @abstractmethod
    def source_format(self) -> FormatVersionInfo:
        """Get the source format this adapter accepts."""
        pass
        
    @property
    @abstractmethod
    def target_format(self) -> FormatVersionInfo:
        """Get the target format this adapter produces."""
        pass
        
    @abstractmethod
    def convert(self, document: Any, **kwargs) -> Any:
        """
        Convert a document from the source format to the target format.
        
        Args:
            document: The document to convert
            **kwargs: Additional parameters for the conversion
            
        Returns:
            Any: The converted document
            
        Raises:
            ValueError: If the document is invalid or conversion fails
        """
        pass


class AdapterRegistry:
    """
    Registry for document format adapters.
    
    The registry maintains a collection of adapter classes and provides
    methods for looking up adapters based on source and target formats.
    """
    
    def __init__(self):
        """Initialize an empty adapter registry."""
        self._adapters: Set[Type[BaseAdapter]] = set()
        
    def register_adapter(self, adapter_class: Type[BaseAdapter]) -> None:
        """
        Register an adapter class with the registry.
        
        Args:
            adapter_class: The adapter class to register
            
        Raises:
            TypeError: If the adapter_class is not a subclass of BaseAdapter
        """
        if not issubclass(adapter_class, BaseAdapter):
            raise TypeError(
                f"Expected a subclass of BaseAdapter, got {adapter_class.__name__}"
            )
            
        self._adapters.add(adapter_class)
        
    def get_adapter_for_formats(
        self,
        source_format: FormatVersionInfo,
        target_format: FormatVersionInfo
    ) -> Optional[Type[BaseAdapter]]:
        """
        Find an adapter that can convert between the specified formats.
        
        Args:
            source_format: The source format to convert from
            target_format: The target format to convert to
            
        Returns:
            Optional[Type[BaseAdapter]]: An adapter class if found, or None
        """
        for adapter_class in self._adapters:
            # Create a temporary instance to check format compatibility
            adapter = adapter_class()
            
            if (source_format.is_compatible_with(adapter.source_format) and
                target_format.is_compatible_with(adapter.target_format)):
                return adapter_class
                
        return None
        
    def get_all_adapters(self) -> List[Type[BaseAdapter]]:
        """
        Get all registered adapter classes.
        
        Returns:
            List[Type[BaseAdapter]]: A list of all registered adapter classes
        """
        return list(self._adapters) 