"""
API routes for report generation and management.
"""
import logging
import os
from datetime import datetime
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.services import get_document_service
from app.reporting.service import ReportService, get_report_service
from app.services.document_processing_service import DocumentProcessingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/generate", response_class=JSONResponse)
async def generate_report(
    background_tasks: BackgroundTasks,
    document_ids: List[str] = Query(..., description="List of document IDs to include in the report"),
    include_tables: bool = Query(True, description="Include tables in report"),
    include_figures: bool = Query(True, description="Include figures in report"),
    db: Session = Depends(get_db),
    document_service: DocumentProcessingService = Depends(get_document_service),
    report_service: ReportService = Depends(get_report_service)
):
    """
    Generate a report for multiple documents.
    
    Args:
        background_tasks: FastAPI background tasks
        document_ids: List of document IDs to include
        include_tables: Whether to include tables
        include_figures: Whether to include figures
        db: Database session
        document_service: Document service instance
        report_service: Report service instance
        
    Returns:
        JSON response with report ID
    """
    # Validate that documents exist
    documents = []
    for doc_id in document_ids:
        document = document_service.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail=f"Document with ID {doc_id} not found")
        documents.append(document)
    
    # Generate a unique report ID
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    report_id = f"report_{timestamp}_{len(document_ids)}"
    
    # Generate report content
    html_content = report_service.generate_report(
        documents=documents,
        include_tables=include_tables,
        include_figures=include_figures
    )
    
    # Save report to file
    report_service.save_report(html_content, report_id)
    
    return {
        "report_id": report_id,
        "document_count": len(documents),
        "report_url": f"/api/reports/{report_id}"
    }

@router.get("/{report_id}", response_class=HTMLResponse)
async def get_report(
    report_id: str,
    report_service: ReportService = Depends(get_report_service)
):
    """
    Get a generated report by ID.
    
    Args:
        report_id: Report ID
        report_service: Report service instance
        
    Returns:
        HTML response with report content
    """
    report_path = os.path.join(report_service.output_dir, f"{report_id}.html")
    
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail=f"Report with ID {report_id} not found")
    
    return FileResponse(report_path)

@router.get("/document/{document_id}", response_class=HTMLResponse)
async def get_document_report(
    document_id: str,
    include_tables: bool = Query(True, description="Include tables in report"),
    include_figures: bool = Query(True, description="Include figures in report"),
    db: Session = Depends(get_db),
    document_service: DocumentProcessingService = Depends(get_document_service),
    report_service: ReportService = Depends(get_report_service)
):
    """
    Generate and serve a report for a single document.
    
    Args:
        document_id: Document ID
        include_tables: Whether to include tables
        include_figures: Whether to include figures
        db: Database session
        document_service: Document service instance
        report_service: Report service instance
        
    Returns:
        HTML response with report content
    """
    # Retrieve document
    document = document_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")
    
    # Generate report
    html_content = report_service.generate_report(
        documents=[document],
        include_tables=include_tables,
        include_figures=include_figures,
        standalone=True
    )
    
    return HTMLResponse(content=html_content, status_code=200) 