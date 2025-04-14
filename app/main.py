"""
Main application module.

This module initializes and configures the FastAPI application.
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.core.config import settings
from app.utils.logging import configure_logging, log_request_details


# Configure logging
configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle events handler.
    
    This context manager is triggered on application startup and shutdown.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Any additional startup logic here (database connections, etc.)
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")
    
    # Any additional cleanup logic here


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    # Initialize FastAPI application
    application = FastAPI(
        title=settings.APP_NAME,
        description="Semantic Reader Backend API",
        version=settings.APP_VERSION,
        openapi_url=f"/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
        debug=settings.DEBUG_MODE
    )
    
    # Add CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add request logging middleware
    @application.middleware("http")
    async def log_requests(request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timer
        start_time = time.time()
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            # Log request details
            log_request_details({
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": process_time
            })
            
            return response
        except Exception as e:
            # Log exception
            logger.exception(f"Unhandled exception in request {request_id}: {str(e)}")
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "message": str(e) if settings.DEBUG_MODE else "An error occurred processing your request"
                }
            )
    
    # Include API router
    application.include_router(api_router, prefix="/api")
    
    # Root endpoint
    @application.get("/", include_in_schema=False)
    async def root():
        """Root endpoint."""
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "api": "/api"
        }
    
    return application


# Create application instance
app = create_application()


# Entry point for uvicorn
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG_MODE,
        log_level=settings.LOG_LEVEL.lower()
    ) 