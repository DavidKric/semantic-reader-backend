"""
Document processing pipeline package.

This package provides a modular pipeline for document processing,
with support for various document processing steps and end-to-end
integration using DoclingDocument as the core data structure.
"""

from papermage_docling.pipeline.pipeline import (
    Pipeline, PipelineStep, DocumentProcessor
)
from papermage_docling.pipeline.simple_pipeline import SimplePipeline

__all__ = [
    "Pipeline",
    "PipelineStep",
    "DocumentProcessor",
    "SimplePipeline"
]

"""
Legacy pipeline compatibility layer.

This module provides stubs and compatibility imports for code that might
still reference the old pipeline classes, which have been removed in favor
of direct Docling integration.

DEPRECATED: These are placeholder compatibility classes that will be removed in a future version.
"""

import warnings
from typing import Any, Dict, List, Optional, Callable

# For compatibility with code that imports Pipeline
class Pipeline:
    """
    Legacy compatibility class for the document processing pipeline.
    
    DEPRECATED: This class is maintained only for backward compatibility.
    """
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "Pipeline is deprecated and will be removed in a future version. "
            "Use the new converter module instead.",
            DeprecationWarning,
            stacklevel=2
        )
    
    def add_step(self, *args, **kwargs):
        """Stub method for compatibility."""
        warnings.warn(
            "Pipeline.add_step is deprecated and will be removed in a future version. "
            "Use the new converter module instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self
    
    def process(self, *args, **kwargs):
        """Stub method for compatibility."""
        warnings.warn(
            "Pipeline.process is deprecated and will be removed in a future version. "
            "Use the new converter module instead.",
            DeprecationWarning,
            stacklevel=2
        )
        from papermage_docling.converter import convert_document
        return convert_document(*args, **kwargs)

# For compatibility with code that imports SimplePipeline
class SimplePipeline(Pipeline):
    """
    Legacy compatibility class for the simple document processing pipeline.
    
    DEPRECATED: This class is maintained only for backward compatibility.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def add_processor(self, *args, **kwargs):
        """Stub method for compatibility."""
        warnings.warn(
            "SimplePipeline.add_processor is deprecated and will be removed in a future version. "
            "Use the new converter module instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self 