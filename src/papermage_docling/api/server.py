"""
FastAPI server for PaperMage Docling API.

This module provides a RESTful API server for accessing document processing
functionality in the PaperMage Docling project.
"""
import os
import tempfile
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from papermage_docling.converter import convert_document
from papermage_docling.api.gateway import process_document, get_supported_formats

# Create FastAPI app
app = FastAPI(
    title="PaperMage Docling API",
    description="API for document processing using Docling with PaperMage compatibility",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "name": "PaperMage Docling API",
        "version": "0.1.0",
        "description": "Document processing API with Docling and PaperMage compatibility",
        "endpoints": [
            "/process",
            "/docs",
            "/redoc",
        ],
    }

@app.post("/process")
async def process_document_endpoint(
    file: UploadFile = File(...),
    output_format: str = Form("papermage"),
    detect_rtl: bool = Form(True),
    enable_ocr: bool = Form(False),
    ocr_language: str = Form("eng"),
    detect_tables: bool = Form(True),
    detect_figures: bool = Form(True),
):
    """
    Process a document and return the parsed content.
    
    Args:
        file: The document file to process
        output_format: Output format ("papermage" or "docling")
        detect_rtl: Whether to detect and process right-to-left text
        enable_ocr: Whether to enable OCR for scanned documents
        ocr_language: OCR language code
        detect_tables: Whether to detect tables
        detect_figures: Whether to detect figures
        
    Returns:
        The processed document data
    """
    # Create a temporary file to store the uploaded file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        # Write the uploaded file content to the temporary file
        temp_file.write(await file.read())
        temp_file_path = temp_file.name
    
    try:
        # Process the document with Docling directly
        options = {
            "detect_rtl": detect_rtl,
            "enable_ocr": enable_ocr,
            "ocr_language": ocr_language,
            "detect_tables": detect_tables,
            "detect_figures": detect_figures,
        }
        
        result = process_document(temp_file_path, options=options)
        
        # If raw Docling output is requested, return directly from converter
        if output_format.lower() == "docling":
            result = convert_document(temp_file_path, options=options, use_legacy=False)
        
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

@app.get("/formats")
def get_formats():
    """Get available document formats."""
    formats = get_supported_formats()
    
    return {
        "formats": [
            {
                "name": "papermage",
                "description": "PaperMage document format",
                "versions": ["1.0", "latest"],
            },
            {
                "name": "docling",
                "description": "Docling document format",
                "versions": ["current"],
            },
        ]
    }

# Import and include recipe_api router
from papermage_docling.api.recipe_api import router as recipe_router
app.include_router(recipe_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 