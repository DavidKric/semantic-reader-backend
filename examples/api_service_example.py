#!/usr/bin/env python3
"""
Example FastAPI service with Recipe API integration.

This script demonstrates how to create a FastAPI service that includes
the Recipe API endpoints for document processing.
"""

import os
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the recipe API router
from papermage_docling.api.recipe_api import router as recipe_router

# Create FastAPI app
app = FastAPI(
    title="PaperMage-Docling API",
    description="API for document processing with PaperMage-compatible recipes",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the recipe router
app.include_router(recipe_router, prefix="/api/v1")

# Add a health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

# Add a root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "PaperMage-Docling API Service",
        "docs": "/docs",
        "recipe_endpoint": "/api/v1/recipe/process"
    }

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "api_service_example:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 