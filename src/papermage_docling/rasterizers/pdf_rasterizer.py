"""
PDF rasterizer module for converting PDF pages to image representations.

This module leverages Docling's native capabilities for generating page images.
"""

import logging
import os
from pathlib import Path
import tempfile
from typing import Dict, List, Optional, Union, Any, Tuple, BinaryIO
import io
from datetime import datetime

try:
    # Import Docling document structures for PDF rendering
    from docling_parse.pdf_parser import PdfDocument
    import fitz  # PyMuPDF
    HAS_DOCLING_PARSE = True
except ImportError:
    logging.warning("Docling dependencies not found. PDF rasterization functionality will be limited.")
    HAS_DOCLING_PARSE = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    logging.warning("PIL not found. Image processing capabilities will be limited.")
    HAS_PIL = False

logger = logging.getLogger(__name__)


class PDFRasterizer:
    """
    PDF rasterizer that converts PDF pages to high-quality images.
    
    This class uses Docling's native PDF rendering capabilities to generate
    images of PDF pages for further processing, such as table and figure
    detection and extraction.
    """
    
    def __init__(
        self,
        dpi: int = 300,
        image_format: str = "png",
        cache_dir: Optional[str] = None,
        use_cache: bool = True,
        **kwargs
    ):
        """
        Initialize the PDF rasterizer with rendering options.
        
        Args:
            dpi: Resolution in dots per inch (higher values produce larger, more detailed images)
            image_format: Output image format ('png' or 'jpg')
            cache_dir: Directory to cache rendered images (None for system temp dir)
            use_cache: Whether to use cached images or always re-render
            **kwargs: Additional rendering options
        """
        self.dpi = dpi
        self.image_format = image_format.lower()
        self.use_cache = use_cache
        self.kwargs = kwargs
        
        # Validate image format
        if self.image_format not in ["png", "jpg", "jpeg"]:
            logger.warning(f"Unsupported image format: {image_format}. Defaulting to png.")
            self.image_format = "png"
        
        # Set up caching
        self.cache_dir = cache_dir
        if self.use_cache:
            if not self.cache_dir:
                self.cache_dir = os.path.join(tempfile.gettempdir(), "docling_rasterizer_cache")
            os.makedirs(self.cache_dir, exist_ok=True)
            logger.info(f"PDF rasterizer cache directory: {self.cache_dir}")
        
        logger.info(f"Initialized PDFRasterizer (dpi: {dpi}, format: {image_format}, use_cache: {use_cache})")
    
    def rasterize_page(
        self, 
        pdf_doc: Union[PdfDocument, str, Path, BinaryIO],
        page_idx: int = 0,
        output_path: Optional[str] = None
    ) -> Tuple[Optional[Image.Image], Dict[str, Any]]:
        """
        Rasterize a single PDF page to an image.
        
        Args:
            pdf_doc: PdfDocument, path to PDF file, or file-like object
            page_idx: Index of the page to rasterize (0-based)
            output_path: Optional path to save the rendered image
            
        Returns:
            Tuple of (image, metadata) where image is the PIL Image and
            metadata contains information about the rendering
        """
        if not HAS_DOCLING_PARSE or not HAS_PIL:
            logger.error("Cannot rasterize PDF pages: required dependencies missing.")
            return None, {"error": "Missing dependencies"}
        
        # Generate cache key if caching is enabled
        cache_key = None
        if self.use_cache:
            if isinstance(pdf_doc, (str, Path)):
                pdf_path = str(pdf_doc)
                file_stat = os.stat(pdf_path)
                cache_key = f"{os.path.basename(pdf_path)}_{file_stat.st_size}_{file_stat.st_mtime}_{page_idx}_{self.dpi}"
            else:
                # For PdfDocument or file-like objects, use timestamp as part of cache key
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                cache_key = f"doc_{timestamp}_{page_idx}_{self.dpi}"
            
            # Check if cached image exists
            if cache_key:
                cached_image_path = os.path.join(self.cache_dir, f"{cache_key}.{self.image_format}")
                if os.path.exists(cached_image_path):
                    try:
                        logger.info(f"Using cached image for page {page_idx+1}: {cached_image_path}")
                        img = Image.open(cached_image_path)
                        metadata = {
                            "page_index": page_idx,
                            "dpi": self.dpi,
                            "format": self.image_format,
                            "width": img.width,
                            "height": img.height,
                            "from_cache": True,
                            "cache_path": cached_image_path
                        }
                        
                        # Save to output path if requested
                        if output_path and output_path != cached_image_path:
                            img.save(output_path)
                            metadata["output_path"] = output_path
                        
                        return img, metadata
                    except Exception as e:
                        logger.warning(f"Failed to load cached image: {e}. Rendering new image.")
        
        # Open PDF document if needed
        doc = None
        try:
            if isinstance(pdf_doc, PdfDocument):
                # Already a PdfDocument, use directly
                doc = pdf_doc
            elif isinstance(pdf_doc, (str, Path)):
                # Path to PDF file
                pdf_path = str(pdf_doc)
                doc = fitz.open(pdf_path)
            elif hasattr(pdf_doc, 'read'):
                # File-like object
                pdf_data = pdf_doc.read()
                doc = fitz.open(stream=pdf_data, filetype="pdf")
            else:
                logger.error(f"Unsupported PDF document type: {type(pdf_doc)}")
                return None, {"error": f"Unsupported PDF document type: {type(pdf_doc)}"}
            
            # Check if page index is valid
            if page_idx < 0 or page_idx >= len(doc):
                logger.error(f"Invalid page index: {page_idx}. Document has {len(doc)} pages.")
                return None, {"error": f"Invalid page index: {page_idx}. Document has {len(doc)} pages."}
            
            # Get the page
            page = doc[page_idx]
            
            # Calculate the pixel dimensions based on DPI
            # 72 points per inch in PDF specification
            zoom = self.dpi / 72
            matrix = fitz.Matrix(zoom, zoom)
            
            # Render the page to a PyMuPDF Pixmap
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            
            # Convert to PIL Image
            img_data = pixmap.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Save the image to cache if enabled
            if self.use_cache and cache_key:
                cache_path = os.path.join(self.cache_dir, f"{cache_key}.{self.image_format}")
                img.save(cache_path, format=self.image_format.upper())
                logger.info(f"Cached rendered image for page {page_idx+1}: {cache_path}")
            
            # Save to output path if requested
            if output_path:
                img.save(output_path, format=self.image_format.upper())
                logger.info(f"Saved rendered image to: {output_path}")
            
            # Create metadata
            metadata = {
                "page_index": page_idx,
                "dpi": self.dpi,
                "format": self.image_format,
                "width": img.width,
                "height": img.height,
                "from_cache": False
            }
            if output_path:
                metadata["output_path"] = output_path
            
            return img, metadata
            
        except Exception as e:
            logger.error(f"Error rasterizing PDF page: {e}")
            return None, {"error": str(e)}
    
    def rasterize_document(
        self, 
        pdf_doc: Union[PdfDocument, str, Path, BinaryIO],
        output_dir: Optional[str] = None,
        start_page: int = 0,
        end_page: Optional[int] = None
    ) -> Dict[int, Dict[str, Any]]:
        """
        Rasterize a range of pages from a PDF document.
        
        Args:
            pdf_doc: PdfDocument, path to PDF file, or file-like object
            output_dir: Directory to save the rendered images
            start_page: First page to render (0-based)
            end_page: Last page to render (0-based, inclusive) or None for all pages
            
        Returns:
            Dictionary mapping page indices to metadata dictionaries
        """
        if not HAS_DOCLING_PARSE or not HAS_PIL:
            logger.error("Cannot rasterize PDF pages: required dependencies missing.")
            return {-1: {"error": "Missing dependencies"}}
        
        results = {}
        
        # Open PDF document if needed
        doc = None
        try:
            if isinstance(pdf_doc, PdfDocument):
                # Already a PdfDocument, use directly
                doc = pdf_doc
            elif isinstance(pdf_doc, (str, Path)):
                # Path to PDF file
                pdf_path = str(pdf_doc)
                doc = fitz.open(pdf_path)
            elif hasattr(pdf_doc, 'read'):
                # File-like object
                pdf_data = pdf_doc.read()
                doc = fitz.open(stream=pdf_data, filetype="pdf")
            else:
                logger.error(f"Unsupported PDF document type: {type(pdf_doc)}")
                return {-1: {"error": f"Unsupported PDF document type: {type(pdf_doc)}"}}
            
            # Determine page range
            max_page = len(doc) - 1
            if end_page is None or end_page > max_page:
                end_page = max_page
            
            if start_page < 0:
                start_page = 0
            
            # Create output directory if needed
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Rasterize each page in the range
            for page_idx in range(start_page, end_page + 1):
                output_path = None
                if output_dir:
                    page_num_str = f"{page_idx+1:04d}"  # Zero-padded page number
                    output_path = os.path.join(output_dir, f"page_{page_num_str}.{self.image_format}")
                
                _, metadata = self.rasterize_page(
                    pdf_doc=doc,
                    page_idx=page_idx,
                    output_path=output_path
                )
                
                results[page_idx] = metadata
            
            logger.info(f"Rasterized {len(results)} pages from PDF document")
            return results
            
        except Exception as e:
            logger.error(f"Error rasterizing PDF document: {e}")
            return {-1: {"error": str(e)}}
    
    def map_pdf_to_image_coordinates(
        self, 
        pdf_coords: Tuple[float, float, float, float],
        page_idx: int,
        pdf_doc: Union[PdfDocument, str, Path, BinaryIO]
    ) -> Tuple[int, int, int, int]:
        """
        Map PDF coordinates to image pixel coordinates.
        
        Args:
            pdf_coords: PDF coordinates as (x0, y0, x1, y1) in PDF points
            page_idx: Page index
            pdf_doc: PdfDocument, path to PDF file, or file-like object
            
        Returns:
            Image coordinates as (x0, y0, x1, y1) in pixels
        """
        if not HAS_DOCLING_PARSE:
            logger.error("Cannot map coordinates: required dependencies missing.")
            return (0, 0, 0, 0)
        
        try:
            # Open PDF document if needed
            doc = None
            if isinstance(pdf_doc, PdfDocument):
                # Already a PdfDocument, use directly
                doc = pdf_doc
            elif isinstance(pdf_doc, (str, Path)):
                # Path to PDF file
                pdf_path = str(pdf_doc)
                doc = fitz.open(pdf_path)
            elif hasattr(pdf_doc, 'read'):
                # File-like object
                pdf_data = pdf_doc.read()
                doc = fitz.open(stream=pdf_data, filetype="pdf")
            else:
                logger.error(f"Unsupported PDF document type: {type(pdf_doc)}")
                return (0, 0, 0, 0)
            
            # Check if page index is valid
            if page_idx < 0 or page_idx >= len(doc):
                logger.error(f"Invalid page index: {page_idx}. Document has {len(doc)} pages.")
                return (0, 0, 0, 0)
            
            # Get the page
            page = doc[page_idx]
            
            # Calculate the scaling factor
            # 72 points per inch in PDF specification
            scale = self.dpi / 72
            
            # Map coordinates
            x0, y0, x1, y1 = pdf_coords
            img_x0 = int(x0 * scale)
            img_y0 = int(y0 * scale)
            img_x1 = int(x1 * scale)
            img_y1 = int(y1 * scale)
            
            return (img_x0, img_y0, img_x1, img_y1)
            
        except Exception as e:
            logger.error(f"Error mapping coordinates: {e}")
            return (0, 0, 0, 0)
    
    def map_image_to_pdf_coordinates(
        self, 
        img_coords: Tuple[int, int, int, int],
        page_idx: int,
        pdf_doc: Union[PdfDocument, str, Path, BinaryIO]
    ) -> Tuple[float, float, float, float]:
        """
        Map image pixel coordinates to PDF coordinates.
        
        Args:
            img_coords: Image coordinates as (x0, y0, x1, y1) in pixels
            page_idx: Page index
            pdf_doc: PdfDocument, path to PDF file, or file-like object
            
        Returns:
            PDF coordinates as (x0, y0, x1, y1) in PDF points
        """
        if not HAS_DOCLING_PARSE:
            logger.error("Cannot map coordinates: required dependencies missing.")
            return (0.0, 0.0, 0.0, 0.0)
        
        try:
            # Calculate the scaling factor
            # 72 points per inch in PDF specification
            scale = 72 / self.dpi
            
            # Map coordinates
            img_x0, img_y0, img_x1, img_y1 = img_coords
            x0 = float(img_x0 * scale)
            y0 = float(img_y0 * scale)
            x1 = float(img_x1 * scale)
            y1 = float(img_y1 * scale)
            
            return (x0, y0, x1, y1)
            
        except Exception as e:
            logger.error(f"Error mapping coordinates: {e}")
            return (0.0, 0.0, 0.0, 0.0)


# Singleton instance for global use
_pdf_rasterizer = None


def get_pdf_rasterizer(
    dpi: int = 300,
    image_format: str = "png",
    use_cache: bool = True,
    **kwargs
) -> PDFRasterizer:
    """
    Get or create a singleton instance of PDFRasterizer.
    
    Args:
        dpi: Resolution in dots per inch
        image_format: Output image format
        use_cache: Whether to use cached images
        **kwargs: Additional rasterizer options
        
    Returns:
        Singleton instance of PDFRasterizer
    """
    global _pdf_rasterizer
    if _pdf_rasterizer is None:
        _pdf_rasterizer = PDFRasterizer(
            dpi=dpi,
            image_format=image_format,
            use_cache=use_cache,
            **kwargs
        )
    return _pdf_rasterizer 