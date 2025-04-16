from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, HttpUrl

class ConvertURLRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL of the document to convert")
    options: Optional[Dict[str, Any]] = Field(None, description="Conversion options")

class DocumentResult(BaseModel):
    id: str
    filename: str
    status: str
    metadata: Optional[Dict[str, Any]] = None

class ConversionOptions(BaseModel):
    detect_tables: bool = True
    detect_figures: bool = True
    enable_ocr: bool = False
    ocr_language: Optional[str] = None
    detect_rtl: bool = True

class ConvertResponse(BaseModel):
    job_id: str
    status: str
    document: Optional[DocumentResult] = None

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: Optional[float] = None
    document: Optional[DocumentResult] = None
