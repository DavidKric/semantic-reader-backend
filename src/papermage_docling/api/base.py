"""
Base classes for API adapters in the PaperMage Docling project.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Type, Any


@dataclass
class FormatVersionInfo:
    """Information about a specific format version supported by an adapter."""
    format_name: str
    version: str
    description: str = ""


class BaseAdapter(ABC):
    """Base class for all API adapters."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the adapter."""
        pass
    
    @property
    @abstractmethod
    def supports_formats(self) -> List[FormatVersionInfo]:
        """List of formats supported by this adapter."""
        pass
    
    @abstractmethod
    def convert(self, data: Any, **kwargs) -> Any:
        """
        Convert data from one format to another.
        
        Args:
            data: The data to convert
            **kwargs: Additional arguments for the conversion
            
        Returns:
            The converted data
        """
        pass
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """
        Validate if the data is in a format supported by this adapter.
        
        Args:
            data: The data to validate
            
        Returns:
            True if the data is valid, False otherwise
        """
        pass


class AdapterRegistry:
    """Registry for API adapters."""
    
    def __init__(self):
        self._adapters: Dict[str, BaseAdapter] = {}
    
    def register(self, adapter: BaseAdapter) -> None:
        """
        Register an adapter.
        
        Args:
            adapter: The adapter to register
        """
        self._adapters[adapter.name] = adapter
    
    def get(self, name: str) -> Optional[BaseAdapter]:
        """
        Get an adapter by name.
        
        Args:
            name: Name of the adapter
            
        Returns:
            The adapter or None if not found
        """
        return self._adapters.get(name)
    
    def list_adapters(self) -> List[str]:
        """
        List all registered adapter names.
        
        Returns:
            List of adapter names
        """
        return list(self._adapters.keys())
    
    def find_adapter_for_format(self, format_name: str, version: Optional[str] = None) -> Optional[BaseAdapter]:
        """
        Find an adapter that supports the given format and version.
        
        Args:
            format_name: Name of the format
            version: Optional version of the format
            
        Returns:
            The adapter or None if not found
        """
        for adapter in self._adapters.values():
            for fmt in adapter.supports_formats:
                if fmt.format_name == format_name:
                    if version is None or fmt.version == version:
                        return adapter
        return None 