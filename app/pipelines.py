"""
Document processing pipelines.

This module provides the core document processing functionality,
handling the conversion of documents from various formats to structured data.
"""

import os
import uuid
import logging
import tempfile
import time
import asyncio
from typing import Dict, List, Any, Optional, Union, BinaryIO
from pathlib import Path
from datetime import datetime

import aiohttp
from fastapi import UploadFile, HTTPException

from papermage_docling.converter import convert_document
from app.config import settings

logger = logging.getLogger(__name__)

# Global job store (in-memory for now, would use Redis or database in production)
class JobStore:
    """Store for processing jobs and results."""
    
    def __init__(self):
        """Initialize the job store."""
        self.jobs: Dict[str, Dict[str, Any]] = {}
    
    def create_job(self, job_id: str) -> None:
        """
        Create a new job in the store.
        
        Args:
            job_id: ID for the new job
        """
        self.jobs[job_id] = {
            "status": "processing",
            "created_at": datetime.now().isoformat()
        }
    
    def update_job(self, job_id: str, data: Dict[str, Any]) -> None:
        """
        Update a job in the store.
        
        Args:
            job_id: ID of the job to update
            data: Data to update in the job
        """
        if job_id in self.jobs:
            self.jobs[job_id].update(data)
            self.jobs[job_id]["updated_at"] = datetime.now().isoformat()
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a job.
        
        Args:
            job_id: ID of the job to check
            
        Returns:
            Job status data or None if not found
        """
        return self.jobs.get(job_id)

# Create a global job store instance
job_store = JobStore()

class DocumentProcessor:
    """Document processor for converting documents to structured data."""
    
    def __init__(self):
        """Initialize the document processor."""
        self.temp_dir = Path(tempfile.gettempdir()) / "papermage_docling"
        self.temp_dir.mkdir(exist_ok=True)
        logger.info(f"Initialized DocumentProcessor with temp directory: {self.temp_dir}")
    
    async def process_url_documents(self, urls: List[str], job_id: str, 
                                    options: Optional[Dict[str, Any]] = None) -> None:
        """
        Process documents from URLs asynchronously.
        
        Args:
            urls: List of document URLs to process
            job_id: ID of the processing job
            options: Processing options
        """
        job_store.create_job(job_id)
        logger.info(f"Processing {len(urls)} documents from URLs for job {job_id}")
        
        results = []
        
        for url in urls:
            try:
                # Download file from URL
                logger.info(f"Downloading document from {url}")
                temp_file = self.temp_dir / f"{uuid.uuid4()}.pdf"
                
                await self._download_file(url, temp_file)
                
                # Process the document
                logger.info(f"Processing downloaded document {temp_file}")
                start_time = time.time()
                
                doc = self._process_document(str(temp_file), options or {})
                
                processing_time = int((time.time() - start_time) * 1000)
                logger.info(f"Document processed in {processing_time}ms")
                
                results.append({
                    "url": url,
                    "document": doc,
                    "status": "success",
                    "processing_time_ms": processing_time
                })
                
                # Clean up
                temp_file.unlink(missing_ok=True)
                
            except Exception as e:
                logger.error(f"Error processing URL {url}: {str(e)}")
                results.append({
                    "url": url,
                    "error": str(e),
                    "status": "failed"
                })
        
        # Store results
        job_store.update_job(job_id, {
            "results": results,
            "status": "completed"
        })
        
        logger.info(f"Completed processing for job {job_id}")
    
    async def process_file_documents(self, files: List[UploadFile], job_id: str,
                                    options: Optional[Dict[str, Any]] = None) -> None:
        """
        Process uploaded documents asynchronously.
        
        Args:
            files: List of uploaded files to process
            job_id: ID of the processing job
            options: Processing options
        """
        job_store.create_job(job_id)
        logger.info(f"Processing {len(files)} uploaded documents for job {job_id}")
        
        results = []
        
        for file in files:
            try:
                # Validate file
                await self._validate_file(file)
                
                # Save to temp file
                content = await file.read()
                temp_file = self.temp_dir / f"{uuid.uuid4()}.pdf"
                temp_file.write_bytes(content)
                
                # Process the document
                logger.info(f"Processing uploaded document {file.filename}")
                start_time = time.time()
                
                doc = self._process_document(str(temp_file), options or {})
                
                processing_time = int((time.time() - start_time) * 1000)
                logger.info(f"Document processed in {processing_time}ms")
                
                results.append({
                    "filename": file.filename,
                    "document": doc,
                    "status": "success",
                    "processing_time_ms": processing_time
                })
                
                # Clean up
                temp_file.unlink(missing_ok=True)
                
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {str(e)}")
                results.append({
                    "filename": file.filename,
                    "error": str(e),
                    "status": "failed"
                })
        
        # Store results
        job_store.update_job(job_id, {
            "results": results,
            "status": "completed"
        })
        
        logger.info(f"Completed processing for job {job_id}")
    
    async def _validate_file(self, file: UploadFile) -> None:
        """
        Validate an uploaded file.
        
        Args:
            file: Uploaded file to validate
            
        Raises:
            HTTPException: If file validation fails
        """
        # Check file extension
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        extension = file.filename.split('.')[-1].lower()
        if extension not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File extension '{extension}' not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
            )
        
        # Check file size
        # Read a small amount to start the file
        content = await file.read(1024)
        size = len(content)
        
        # Seek to end to get size
        current_position = file.file.tell()
        await file.seek(0, 2)  # Seek to end
        size = file.file.tell()
        await file.seek(0)  # Reset to beginning
        
        max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if size > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
            )
    
    async def _download_file(self, url: str, dest_path: Path) -> None:
        """
        Download a file from a URL.
        
        Args:
            url: URL to download from
            dest_path: Path to save the downloaded file
            
        Raises:
            HTTPException: If download fails
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        raise HTTPException(
                            status_code=502,
                            detail=f"Failed to download file: HTTP {response.status}"
                        )
                    
                    content = await response.read()
                    dest_path.write_bytes(content)
                    
            except aiohttp.ClientError as e:
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to download file: {str(e)}"
                )
    
    def _process_document(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a document using Docling conversion.
        
        Args:
            file_path: Path to the document file
            options: Processing options
            
        Returns:
            Processed document data
            
        Raises:
            HTTPException: If processing fails
        """
        try:
            # Configure conversion options
            conversion_options = {
                "enable_ocr": options.get("perform_ocr", settings.OCR_ENABLED),
                "ocr_language": options.get("ocr_language", settings.OCR_LANGUAGE),
                "detect_rtl": options.get("detect_rtl", settings.DETECT_RTL),
                "detect_tables": options.get("extract_tables", True),
                "detect_figures": options.get("extract_figures", True),
            }
            
            # Process the document using Docling directly
            return convert_document(file_path, conversion_options)
                
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process document: {str(e)}"
            )

# Create a global processor instance
document_processor = DocumentProcessor() 