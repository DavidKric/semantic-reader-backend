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