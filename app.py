#!/usr/bin/env python3
"""
Main FastAPI application entry point.

This follows UV best practices for FastAPI application structure.
See: https://docs.astral.sh/uv/guides/integration/fastapi/
"""

import os
import sys
from fastapi import FastAPI
from app import config
from app.api import router as api_router

# Create FastAPI app
app = FastAPI(
    title=config.APP_NAME,
    description=config.APP_DESCRIPTION,
    version=config.APP_VERSION,
)

# Include API routers
app.include_router(api_router)

# Import and include papermage_docling API routers if needed
try:
    # We only try to import these if they exist
    from src.papermage_docling.api import router as docling_router
    app.include_router(docling_router, prefix="/papermage", tags=["papermage"])
except ImportError:
    # This is optional, so we continue without it if not available
    pass

# Entry point for uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
    ) 