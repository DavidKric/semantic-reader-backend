#!/usr/bin/env python3
"""
FastAPI application entry point.

This follows uv and FastAPI best practices for application structure.
Imports the app instance from the restructured package.
"""

import os
import sys

# Import the application instance from the new structure
from app.main import app as application

# Export app for ASGI servers
app = application

# Direct execution for development
if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings
    
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG_MODE,
        log_level=settings.LOG_LEVEL.lower()
    ) 