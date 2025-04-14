"""
Main application module.

This module sets up the FastAPI application with middleware, routers,
and other configurations needed for the API service.
"""

import logging
import time
from typing import Callable, Dict, Optional

import uvicorn
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import gradio as gr

from app.config import settings
from app.api import health, convert, recipe

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    # Create FastAPI application
    application = FastAPI(
        title=settings.APP_NAME,
        description="PDF document processing API with PaperMage-compatible recipe support",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"/{settings.API_VERSION}/openapi.json",
        debug=settings.DEBUG_MODE
    )
    
    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add request ID middleware
    @application.middleware("http")
    async def add_request_id(request: Request, call_next: Callable) -> Response:
        import uuid
        request_id = str(uuid.uuid4())
        logger.debug(f"Request {request_id}: {request.method} {request.url.path}")
        
        # Start timer
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        logger.debug(f"Request {request_id} completed in {process_time:.4f}s")
        return response
    
    # Add rate limiting middleware if enabled
    if settings.RATE_LIMIT_ENABLED:
        try:
            from slowapi import Limiter
            from slowapi.middleware import SlowAPIMiddleware
            from slowapi.errors import RateLimitExceeded
            
            limiter = Limiter(key_func=lambda _: "user")  # Replace with actual user identification
            application.state.limiter = limiter
            application.add_middleware(SlowAPIMiddleware)
            
            @application.exception_handler(RateLimitExceeded)
            async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded",
                        "retry_after": exc.retry_after
                    }
                )
                
            logger.info("Rate limiting middleware enabled")
        except ImportError:
            logger.warning("SlowAPI not installed, rate limiting disabled")
    
    # Add exception handler for HTTPException
    @application.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "message": str(exc) if settings.DEBUG_MODE else "An unexpected error occurred"
            }
        )
    
    # Include routers
    application.include_router(health.router)
    application.include_router(convert.router)
    application.include_router(recipe.router)
    
    # Add Gradio UI if enabled
    if settings.ENABLE_UI:
        try:
            # Create Gradio interface
            with gr.Blocks(title="PDF Processing UI") as ui:
                gr.Markdown("# PDF Document Processing")
                
                with gr.Tab("File Upload"):
                    with gr.Row():
                        with gr.Column():
                            file_input = gr.File(label="Upload PDF")
                            process_btn = gr.Button("Process Document")
                        with gr.Column():
                            result_json = gr.JSON(label="Processing Result")
                    
                    process_btn.click(
                        fn=lambda f: {"message": "Processing started", "file": f.name if f else None},
                        inputs=file_input,
                        outputs=result_json
                    )
                
                with gr.Tab("URL Processing"):
                    with gr.Row():
                        with gr.Column():
                            url_input = gr.Textbox(label="PDF URL", placeholder="https://example.com/document.pdf")
                            url_process_btn = gr.Button("Process URL")
                        with gr.Column():
                            url_result = gr.JSON(label="Processing Result")
                    
                    url_process_btn.click(
                        fn=lambda u: {"message": "URL processing started", "url": u},
                        inputs=url_input,
                        outputs=url_result
                    )
            
            # Mount Gradio app
            application.mount("/ui", gr.routes.App.create_app(ui))
            logger.info("Gradio UI enabled at /ui")
        except ImportError:
            logger.warning("Gradio not installed, UI disabled")
    
    logger.info(f"Application {settings.APP_NAME} initialized")
    return application

# Create the application instance
app = create_application()

@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_check": "/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG_MODE,
        workers=settings.WORKERS_COUNT,
        log_level=settings.LOG_LEVEL.lower()
    ) 