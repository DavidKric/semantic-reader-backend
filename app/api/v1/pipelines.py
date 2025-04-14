"""
Document processing pipeline endpoints for the application.

This module provides endpoints for pipeline configuration, status,
and statistics related to the document processing pipeline.
"""

import logging
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Query, status, Body
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.schemas.base import BaseSchema
from app.services.pipeline_service import PipelineService

# Import papermage_docling API service and pipeline
try:
    from papermage_docling.api_service import get_api_service
    from papermage_docling.pipeline import SimplePipeline, Pipeline
    DOCLING_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("papermage_docling not available. Pipeline features will be disabled.")
    DOCLING_AVAILABLE = False

router = APIRouter()
logger = logging.getLogger(__name__)


class PipelineConfigResponse(BaseSchema):
    """Response model for pipeline configuration."""
    status: str = "success"
    pipeline_type: str
    steps: List[str]
    config: Dict[str, Any]
    predictors: Optional[Dict[str, Any]] = None


class PipelineStatsResponse(BaseSchema):
    """Response model for pipeline statistics."""
    status: str = "success"
    total_processed: int
    processing_times: Dict[str, Any]
    step_stats: Dict[str, Any]
    error_counts: Dict[str, int]


class PredictorConfigResponse(BaseSchema):
    """Response model for predictor configuration."""
    status: str = "success"
    predictor_type: str
    config: Dict[str, Any]


class AnalysisResponse(BaseSchema):
    """Response model for document analysis."""
    status: str = "success"
    document_id: str
    analysis_type: str
    results: Dict[str, Any]


def get_pipeline_service():
    """Dependency for pipeline service."""
    return PipelineService()


@router.get(
    "/config",
    response_model=PipelineConfigResponse,
    status_code=status.HTTP_200_OK,
    tags=["pipelines"],
    summary="Get Pipeline Configuration",
    description="Get the current document processing pipeline configuration"
)
async def get_pipeline_config(
    pipeline_service: PipelineService = Depends(get_pipeline_service)
) -> PipelineConfigResponse:
    """
    Get the current document processing pipeline configuration.
    
    Returns:
        The pipeline configuration
    """
    # Check if papermage_docling is available
    if not DOCLING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Document processing pipeline is not available"
        )
    
    try:
        # Get pipeline configuration
        config = pipeline_service.get_pipeline_config()
        
        return PipelineConfigResponse(
            status="success",
            pipeline_type=config["pipeline_type"],
            steps=config["steps"],
            config=config["config"],
            predictors=config["predictors"]
        )
            
    except Exception as e:
        logger.exception(f"Error getting pipeline configuration: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting pipeline configuration: {str(e)}"
        )


@router.post(
    "/configure-predictor",
    response_model=PredictorConfigResponse,
    status_code=status.HTTP_200_OK,
    tags=["pipelines"],
    summary="Configure Predictor",
    description="Configure a specific predictor in the document processing pipeline"
)
async def configure_predictor(
    predictor_type: str = Query(..., description="Predictor type (structure, figure, table, language)"),
    config: Dict[str, Any] = Body(..., description="Configuration parameters"),
    pipeline_service: PipelineService = Depends(get_pipeline_service)
) -> PredictorConfigResponse:
    """
    Configure a specific predictor.
    
    Args:
        predictor_type: The type of predictor (structure, figure, table, language)
        config: Configuration parameters
        
    Returns:
        Updated predictor configuration
    """
    # Check if papermage_docling is available
    if not DOCLING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Document processing pipeline is not available"
        )
    
    try:
        # Configure predictor
        updated_config = pipeline_service.configure_predictor(predictor_type, config)
        
        return PredictorConfigResponse(
            status="success",
            predictor_type=predictor_type,
            config=updated_config
        )
            
    except ValueError as e:
        logger.warning(f"Invalid predictor configuration: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error configuring predictor: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error configuring predictor: {str(e)}"
        )


@router.post(
    "/customize",
    response_model=PipelineConfigResponse,
    status_code=status.HTTP_200_OK,
    tags=["pipelines"],
    summary="Customize Pipeline",
    description="Customize the document processing pipeline by adding/removing steps"
)
async def customize_pipeline(
    steps: List[str] = Body(..., description="Ordered list of pipeline step names to enable"),
    parameters: Dict[str, Any] = Body({}, description="Pipeline-wide parameters"),
    pipeline_service: PipelineService = Depends(get_pipeline_service)
) -> PipelineConfigResponse:
    """
    Customize the document processing pipeline.
    
    Args:
        steps: Ordered list of pipeline step names to enable
        parameters: Pipeline-wide parameters
        
    Returns:
        Updated pipeline configuration
    """
    # Check if papermage_docling is available
    if not DOCLING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Document processing pipeline is not available"
        )
    
    try:
        # Customize pipeline
        config = pipeline_service.customize_pipeline(steps, parameters)
        
        return PipelineConfigResponse(
            status="success",
            pipeline_type=config["pipeline_type"],
            steps=config["steps"],
            config=config["config"],
            predictors=config["predictors"]
        )
            
    except ValueError as e:
        logger.warning(f"Invalid pipeline configuration: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error customizing pipeline: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error customizing pipeline: {str(e)}"
        )


@router.get(
    "/stats",
    response_model=PipelineStatsResponse,
    status_code=status.HTTP_200_OK,
    tags=["pipelines"],
    summary="Get Pipeline Statistics",
    description="Get statistics about the document processing pipeline"
)
async def get_pipeline_stats(
    pipeline_service: PipelineService = Depends(get_pipeline_service)
) -> PipelineStatsResponse:
    """
    Get statistics about the document processing pipeline.
    
    Returns:
        Pipeline processing statistics
    """
    # Check if papermage_docling is available
    if not DOCLING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Document processing pipeline is not available"
        )
    
    try:
        # Get pipeline statistics
        stats = pipeline_service.get_pipeline_stats()
        
        # Return formatted statistics
        return PipelineStatsResponse(
            status="success",
            total_processed=stats.get("total_processed", 0),
            processing_times=stats.get("processing_times", {}),
            step_stats=stats.get("step_stats", {}),
            error_counts=stats.get("error_counts", {})
        )
            
    except Exception as e:
        logger.exception(f"Error getting pipeline statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting pipeline statistics: {str(e)}"
        )


@router.post(
    "/analyze/{document_id}",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    tags=["pipelines"],
    summary="Analyze Document",
    description="Perform analysis on a document using the pipeline"
)
async def analyze_document(
    document_id: str,
    analysis_type: str = Query(..., description="Type of analysis (language, structure, tables, figures)"),
    parameters: Dict[str, Any] = Body({}, description="Analysis parameters"),
    pipeline_service: PipelineService = Depends(get_pipeline_service)
) -> AnalysisResponse:
    """
    Perform analysis on a document.
    
    Args:
        document_id: The document ID
        analysis_type: Type of analysis to perform
        parameters: Analysis parameters
        
    Returns:
        Analysis results
    """
    # Check if papermage_docling is available
    if not DOCLING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Document processing pipeline is not available"
        )
    
    try:
        # Perform analysis
        results = pipeline_service.analyze_document(document_id, analysis_type, parameters)
        
        return AnalysisResponse(
            status="success",
            document_id=document_id,
            analysis_type=analysis_type,
            results=results
        )
            
    except ValueError as e:
        logger.warning(f"Invalid analysis request: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error analyzing document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing document: {str(e)}"
        )


@router.get(
    "/cache-stats",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    tags=["pipelines"],
    summary="Get Cache Statistics",
    description="Get statistics about the document cache"
)
async def get_cache_stats(
    pipeline_service: PipelineService = Depends(get_pipeline_service)
) -> Dict[str, Any]:
    """
    Get statistics about the document cache.
    
    Returns:
        Cache statistics
    """
    # Check if papermage_docling is available
    if not DOCLING_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Document processing pipeline is not available"
        )
    
    try:
        # Get cache statistics from pipeline service
        return pipeline_service.api_service.get_cache_stats()
            
    except Exception as e:
        logger.exception(f"Error getting cache statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting cache statistics: {str(e)}"
        ) 