"""
Document analysis endpoints for the application.

This module provides endpoints for various types of document analysis
such as language detection, structure analysis, table detection, etc.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from app.schemas.document_entities import (
    FigureAnalysisResult,
    LanguageAnalysisResult,
    StructureAnalysisResult,
    TableAnalysisResult,
)
from app.services.analysis_service import AnalysisService

# Import papermage_docling components if available
try:
    import papermage_docling
    DOCLING_AVAILABLE = True
except ImportError:
    logging.warning("papermage_docling not available. Analysis features will be disabled.")
    DOCLING_AVAILABLE = False

router = APIRouter()
logger = logging.getLogger(__name__)


def get_analysis_service():
    """Dependency for analysis service."""
    return AnalysisService()


@router.post(
    "/language/{document_id}",
    response_model=LanguageAnalysisResult,
    status_code=status.HTTP_200_OK,
    tags=["analysis"],
    summary="Language Analysis",
    description="Analyze the language(s) used in a document. Accepts advanced pipeline options via 'options' body param."
)
async def analyze_language(
    document_id: str,
    min_confidence: float = Query(0.2, description="Minimum confidence threshold for language detection"),
    options: Optional[Dict[str, Any]] = Body(None, description="Advanced Docling pipeline options (optional)"),
    analysis_service: AnalysisService = Depends(get_analysis_service)
) -> LanguageAnalysisResult:
    """
    Analyze the language(s) used in a document.
    Accepts advanced pipeline options via 'options' body param.
    """
    if not DOCLING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Document analysis features are not available"
        )
    try:
        opts = options or {}
        opts["min_confidence"] = min_confidence
        results = analysis_service.analyze_language(document_id, **opts)
        return LanguageAnalysisResult(**results)
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
    description="Analyze the structure of a document (sections, paragraphs, etc.). Accepts advanced pipeline options via 'options' body param."
)
async def analyze_structure(
    document_id: str,
    detailed: bool = Query(False, description="Whether to include detailed structure analysis"),
    options: Optional[Dict[str, Any]] = Body(None, description="Advanced Docling pipeline options (optional)"),
    analysis_service: AnalysisService = Depends(get_analysis_service)
) -> StructureAnalysisResult:
    """
    Analyze the structure of a document.
    Accepts advanced pipeline options via 'options' body param.
    """
    if not DOCLING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Document analysis features are not available"
        )
    try:
        opts = options or {}
        opts["detailed"] = detailed
        results = analysis_service.analyze_structure(document_id, **opts)
        return StructureAnalysisResult(**results)
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
    description="Analyze tables in a document. Accepts advanced pipeline options via 'options' body param."
)
async def analyze_tables(
    document_id: str,
    include_data: bool = Query(False, description="Whether to include table data in results"),
    options: Optional[Dict[str, Any]] = Body(None, description="Advanced Docling pipeline options (optional)"),
    analysis_service: AnalysisService = Depends(get_analysis_service)
) -> TableAnalysisResult:
    """
    Analyze tables in a document.
    Accepts advanced pipeline options via 'options' body param.
    """
    if not DOCLING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Document analysis features are not available"
        )
    try:
        opts = options or {}
        opts["include_data"] = include_data
        results = analysis_service.analyze_tables(document_id, **opts)
        return TableAnalysisResult(**results)
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
    description="Analyze figures (images, charts, diagrams) in a document. Accepts advanced pipeline options via 'options' body param."
)
async def analyze_figures(
    document_id: str,
    options: Optional[Dict[str, Any]] = Body(None, description="Advanced Docling pipeline options (optional)"),
    analysis_service: AnalysisService = Depends(get_analysis_service)
) -> FigureAnalysisResult:
    """
    Analyze figures in a document.
    Accepts advanced pipeline options via 'options' body param.
    """
    if not DOCLING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Document analysis features are not available"
        )
    try:
        opts = options or {}
        results = analysis_service.analyze_figures(document_id, **opts)
        return FigureAnalysisResult(**results)
    except Exception as e:
        logger.exception(f"Error analyzing document figures: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing document figures: {str(e)}"
        ) 