"""
Document analysis endpoints for the application.

This module provides endpoints for various types of document analysis
such as language detection, structure analysis, table detection, etc.
"""

import logging
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Query, status, Body
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.services.pipeline_service import PipelineService
from app.services.document_processing_service import DocumentProcessingService
from app.schemas.document_entities import (
    StructureAnalysisResult,
    LanguageAnalysisResult,
    TableAnalysisResult,
    FigureAnalysisResult
)

# Import papermage_docling components if available
try:
    import papermage_docling
    DOCLING_AVAILABLE = True
except ImportError:
    logging.warning("papermage_docling not available. Analysis features will be disabled.")
    DOCLING_AVAILABLE = False

router = APIRouter()
logger = logging.getLogger(__name__)


def get_pipeline_service():
    """Dependency for pipeline service."""
    return PipelineService()


def get_document_service():
    """Dependency for document service."""
    return DocumentProcessingService()


@router.post(
    "/language/{document_id}",
    response_model=LanguageAnalysisResult,
    status_code=status.HTTP_200_OK,
    tags=["analysis"],
    summary="Language Analysis",
    description="Analyze the language(s) used in a document"
)
async def analyze_language(
    document_id: str,
    min_confidence: float = Query(0.2, description="Minimum confidence threshold for language detection"),
    pipeline_service: PipelineService = Depends(get_pipeline_service)
) -> LanguageAnalysisResult:
    """
    Analyze the language(s) used in a document.
    
    Args:
        document_id: The document ID
        min_confidence: Minimum confidence threshold for language detection
        
    Returns:
        Language analysis results
    """
    # Check if papermage_docling is available
    if not DOCLING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Document analysis features are not available"
        )
    
    try:
        # Perform language analysis
        results = pipeline_service.analyze_document(
            document_id, 
            "language", 
            {"min_confidence": min_confidence}
        )
        
        return LanguageAnalysisResult(
            document_language=results["document_language"],
            language_name=results["language_name"],
            confidence=results["confidence"],
            is_rtl=results["is_rtl"],
            additional_languages=results["additional_languages"]
        )
            
    except ValueError as e:
        logger.warning(f"Invalid analysis request: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error analyzing document language: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing document language: {str(e)}"
        )


@router.post(
    "/structure/{document_id}",
    response_model=StructureAnalysisResult,
    status_code=status.HTTP_200_OK,
    tags=["analysis"],
    summary="Structure Analysis",
    description="Analyze the structure of a document (sections, paragraphs, etc.)"
)
async def analyze_structure(
    document_id: str,
    detailed: bool = Query(False, description="Whether to include detailed structure analysis"),
    pipeline_service: PipelineService = Depends(get_pipeline_service)
) -> StructureAnalysisResult:
    """
    Analyze the structure of a document.
    
    Args:
        document_id: The document ID
        detailed: Whether to include detailed structure analysis
        
    Returns:
        Structure analysis results
    """
    # Check if papermage_docling is available
    if not DOCLING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Document analysis features are not available"
        )
    
    try:
        # Perform structure analysis
        results = pipeline_service.analyze_document(
            document_id, 
            "structure", 
            {"detailed": detailed}
        )
        
        return StructureAnalysisResult(
            sections_count=results["sections_count"],
            paragraphs_count=results["paragraphs_count"],
            structure_hierarchy=results["structure_hierarchy"]
        )
            
    except ValueError as e:
        logger.warning(f"Invalid analysis request: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error analyzing document structure: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing document structure: {str(e)}"
        )


@router.post(
    "/tables/{document_id}",
    response_model=TableAnalysisResult,
    status_code=status.HTTP_200_OK,
    tags=["analysis"],
    summary="Table Analysis",
    description="Analyze tables in a document"
)
async def analyze_tables(
    document_id: str,
    include_data: bool = Query(False, description="Whether to include table data in results"),
    pipeline_service: PipelineService = Depends(get_pipeline_service)
) -> TableAnalysisResult:
    """
    Analyze tables in a document.
    
    Args:
        document_id: The document ID
        include_data: Whether to include table data in results
        
    Returns:
        Table analysis results
    """
    # Check if papermage_docling is available
    if not DOCLING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Document analysis features are not available"
        )
    
    try:
        # Perform table analysis
        results = pipeline_service.analyze_document(
            document_id, 
            "tables", 
            {"include_data": include_data}
        )
        
        return TableAnalysisResult(
            tables_count=results["tables_count"],
            tables_by_page=results["tables_by_page"]
        )
            
    except ValueError as e:
        logger.warning(f"Invalid analysis request: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error analyzing document tables: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing document tables: {str(e)}"
        )


@router.post(
    "/figures/{document_id}",
    response_model=FigureAnalysisResult,
    status_code=status.HTTP_200_OK,
    tags=["analysis"],
    summary="Figure Analysis",
    description="Analyze figures (images, charts, diagrams) in a document"
)
async def analyze_figures(
    document_id: str,
    pipeline_service: PipelineService = Depends(get_pipeline_service)
) -> FigureAnalysisResult:
    """
    Analyze figures in a document.
    
    Args:
        document_id: The document ID
        
    Returns:
        Figure analysis results
    """
    # Check if papermage_docling is available
    if not DOCLING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Document analysis features are not available"
        )
    
    try:
        # Perform figure analysis
        results = pipeline_service.analyze_document(
            document_id, 
            "figures", 
            {}
        )
        
        return FigureAnalysisResult(
            figures_count=results["figures_count"],
            figures_by_page=results["figures_by_page"]
        )
            
    except ValueError as e:
        logger.warning(f"Invalid analysis request: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error analyzing document figures: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing document figures: {str(e)}"
        ) 