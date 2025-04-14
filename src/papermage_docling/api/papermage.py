"""
Adapters for the PaperMage API formats.
"""
from typing import Any, Dict, List, Optional

from .base import BaseAdapter, FormatVersionInfo, AdapterRegistry


class PaperMageAdapter(BaseAdapter):
    """Base adapter for PaperMage formats."""
    
    @property
    def name(self) -> str:
        """Name of the adapter."""
        return "papermage"
    
    @property
    def supports_formats(self) -> List[FormatVersionInfo]:
        """List of formats supported by this adapter."""
        return [
            FormatVersionInfo(
                format_name="papermage",
                version="*",
                description="Generic PaperMage format adapter"
            )
        ]
    
    def convert(self, data: Any, **kwargs) -> Dict[str, Any]:
        """
        Convert between PaperMage and Docling formats.
        
        Args:
            data: The data to convert
            **kwargs: Additional arguments for the conversion
            
        Returns:
            The converted data
        """
        # This is a placeholder implementation
        return data
    
    def validate(self, data: Any) -> bool:
        """
        Validate if the data is in a PaperMage format.
        
        Args:
            data: The data to validate
            
        Returns:
            True if the data is valid, False otherwise
        """
        if not isinstance(data, dict):
            return False
            
        if "version" not in data:
            return False
            
        if "document" not in data:
            return False
            
        return True


class PaperMageV1Adapter(BaseAdapter):
    """Adapter for PaperMage v1 format."""
    
    @property
    def name(self) -> str:
        """Name of the adapter."""
        return "papermage_v1"
    
    @property
    def supports_formats(self) -> List[FormatVersionInfo]:
        """List of formats supported by this adapter."""
        return [
            FormatVersionInfo(
                format_name="papermage",
                version="1.0",
                description="PaperMage format version 1.0"
            )
        ]
    
    def convert(self, data: Any, **kwargs) -> Dict[str, Any]:
        """
        Convert Docling data to PaperMage v1 format.
        
        Args:
            data: Docling document data
            **kwargs: Additional arguments for the conversion
            
        Returns:
            Data in PaperMage v1 format
        """
        # This is a placeholder implementation
        # In a real implementation, this would convert between formats
        return {
            "version": "1.0",
            "document": {
                "pages": self._convert_pages(data.get("pages", [])),
                "metadata": self._convert_metadata(data.get("metadata", {})),
            }
        }
    
    def validate(self, data: Any) -> bool:
        """
        Validate if the data is in PaperMage v1 format.
        
        Args:
            data: The data to validate
            
        Returns:
            True if the data is valid, False otherwise
        """
        # This is a simplified validation
        if not isinstance(data, dict):
            return False
            
        if data.get("version") != "1.0":
            return False
            
        if "document" not in data:
            return False
            
        if "pages" not in data["document"]:
            return False
            
        return True
    
    def _convert_pages(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert Docling pages to PaperMage pages.
        
        Args:
            pages: Docling pages data
            
        Returns:
            PaperMage pages data
        """
        # Placeholder implementation
        return [self._convert_page(page) for page in pages]
    
    def _convert_page(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a single Docling page to PaperMage page.
        
        Args:
            page: Docling page data
            
        Returns:
            PaperMage page data
        """
        # Placeholder implementation
        return {
            "number": page.get("number", 0),
            "width": page.get("width", 0),
            "height": page.get("height", 0),
            "blocks": self._convert_blocks(page.get("blocks", [])),
        }
    
    def _convert_blocks(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert Docling blocks to PaperMage blocks.
        
        Args:
            blocks: Docling blocks data
            
        Returns:
            PaperMage blocks data
        """
        # Placeholder implementation
        return [self._convert_block(block) for block in blocks]
    
    def _convert_block(self, block: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a single Docling block to PaperMage block.
        
        Args:
            block: Docling block data
            
        Returns:
            PaperMage block data
        """
        # Placeholder implementation
        return {
            "id": block.get("id", ""),
            "type": block.get("type", "text"),
            "bbox": block.get("bbox", [0, 0, 0, 0]),
            "text": block.get("text", ""),
            "confidence": block.get("confidence", 1.0),
        }
    
    def _convert_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Docling metadata to PaperMage metadata.
        
        Args:
            metadata: Docling metadata
            
        Returns:
            PaperMage metadata
        """
        # Placeholder implementation
        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "date": metadata.get("date", ""),
        }


class PaperMageLatestAdapter(PaperMageV1Adapter):
    """Adapter for the latest PaperMage format (currently v1)."""
    
    @property
    def name(self) -> str:
        """Name of the adapter."""
        return "papermage_latest"
    
    @property
    def supports_formats(self) -> List[FormatVersionInfo]:
        """List of formats supported by this adapter."""
        return [
            FormatVersionInfo(
                format_name="papermage",
                version="latest",
                description="Latest PaperMage format"
            )
        ]


# Function to register default adapters
def register_default_adapters(registry: AdapterRegistry) -> None:
    """
    Register default PaperMage adapters with the given registry.
    
    Args:
        registry: The adapter registry to register adapters with
    """
    registry.register(PaperMageAdapter())
    registry.register(PaperMageV1Adapter())
    registry.register(PaperMageLatestAdapter())


# Register the adapters when this module is imported
papermage_adapter_registry = AdapterRegistry()
register_default_adapters(papermage_adapter_registry) 