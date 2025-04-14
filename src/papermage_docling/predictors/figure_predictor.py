"""
Figure detection and extraction using Docling's native capabilities.

This module provides functionality for detecting and extracting figures from
documents and analyzing their contents using Docling's figure extraction.
"""

import logging
import os
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple, BinaryIO
import io
import base64

# Import Docling document structures
try:
    from docling_parse.pdf_parser import PdfDocument
    from docling_core.types.doc.page import SegmentedPage as Page
    from docling_core.types.doc import ImageRef
    # Import figure models if available
    try:
        from docling.models.document_picture_classifier import DocumentPictureClassifier
        HAS_FIGURE_MODELS = True
    except ImportError:
        logging.warning("Docling figure models not found. Using basic figure detection.")
        HAS_FIGURE_MODELS = False
except ImportError:
    logging.warning("Docling dependencies not found. Figure prediction functionality will be limited.")
    # Define stub classes for type hints
    
    class PdfDocument:
        pass
    
    class Page:
        pass
    
    class ImageRef:
        pass
    
    HAS_FIGURE_MODELS = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    logging.warning("PIL not found. Image processing capabilities will be limited.")
    HAS_PIL = False

# Import rasterizer for image processing
from papermage_docling.rasterizers import PDFRasterizer, get_pdf_rasterizer

logger = logging.getLogger(__name__)


class FigureItem:
    """
    Represents a figure with its metadata and content.
    
    This class encapsulates a figure's metadata, content (image data),
    and related information like captions.
    """
    
    def __init__(
        self,
        page_idx: int,
        figure_idx: int,
        bbox: Tuple[float, float, float, float],
        image_data: Optional[bytes] = None,
        image_format: str = "png",
        confidence: float = 0.0
    ):
        """
        Initialize a figure item with its metadata and content.
        
        Args:
            page_idx: Page index where the figure appears
            figure_idx: Index of the figure on the page
            bbox: Bounding box of the figure (x0, y0, x1, y1) in PDF coordinates
            image_data: Raw binary image data
            image_format: Format of the image data ('png', 'jpg', etc.)
            confidence: Detection confidence score (0.0 to 1.0)
        """
        self.page_idx = page_idx
        self.figure_idx = figure_idx
        self.bbox = bbox
        self.image_data = image_data
        self.image_format = image_format.lower()
        self.confidence = confidence
        self.caption = None
        self.metadata = {}
        self.figure_type = "unknown"  # e.g., 'photo', 'chart', 'diagram'
    
    def set_caption(self, caption_text: str, caption_bbox: Optional[Tuple[float, float, float, float]] = None) -> None:
        """
        Set the caption for this figure.
        
        Args:
            caption_text: Text of the caption
            caption_bbox: Optional bounding box of the caption
        """
        self.caption = {
            "text": caption_text,
            "bbox": caption_bbox
        }
    
    def set_figure_type(self, figure_type: str) -> None:
        """
        Set the type of figure.
        
        Args:
            figure_type: Type of figure (e.g., 'photo', 'chart', 'diagram')
        """
        self.figure_type = figure_type
    
    def get_image(self) -> Optional[Image.Image]:
        """
        Get the figure as a PIL Image.
        
        Returns:
            PIL Image or None if image data is not available
        """
        if not HAS_PIL or not self.image_data:
            return None
        
        try:
            return Image.open(io.BytesIO(self.image_data))
        except Exception as e:
            logger.error(f"Error loading image data: {e}")
            return None
    
    def save_image(self, output_path: str) -> bool:
        """
        Save the figure to a file.
        
        Args:
            output_path: Path to save the image
            
        Returns:
            True if successful, False otherwise
        """
        if not self.image_data:
            logger.error("No image data to save")
            return False
        
        try:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(self.image_data)
            return True
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            return False
    
    def get_data_uri(self) -> Optional[str]:
        """
        Get the image as a data URI.
        
        Returns:
            Data URI string or None if image data is not available
        """
        if not self.image_data:
            return None
        
        mime_type = f"image/{self.image_format}"
        data_b64 = base64.b64encode(self.image_data).decode('ascii')
        return f"data:{mime_type};base64,{data_b64}"
    
    def get_hash(self) -> str:
        """
        Get a hash of the image data for deduplication.
        
        Returns:
            MD5 hash of the image data or empty string if no data
        """
        if not self.image_data:
            return ""
        
        return hashlib.md5(self.image_data).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the figure to a dictionary representation.
        
        Returns:
            Dictionary representation of the figure
        """
        # Convert image data to base64 for JSON serialization
        image_data_b64 = None
        if self.image_data:
            image_data_b64 = base64.b64encode(self.image_data).decode('ascii')
        
        return {
            "page_idx": self.page_idx,
            "figure_idx": self.figure_idx,
            "bbox": self.bbox,
            "image_data_b64": image_data_b64,
            "image_format": self.image_format,
            "confidence": self.confidence,
            "caption": self.caption,
            "figure_type": self.figure_type,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FigureItem':
        """
        Create a FigureItem from a dictionary representation.
        
        Args:
            data: Dictionary representation of the figure
            
        Returns:
            FigureItem instance
        """
        # Convert base64 image data back to bytes
        image_data = None
        if data.get("image_data_b64"):
            image_data = base64.b64decode(data["image_data_b64"])
        
        figure = cls(
            page_idx=data.get("page_idx", 0),
            figure_idx=data.get("figure_idx", 0),
            bbox=data.get("bbox", (0, 0, 0, 0)),
            image_data=image_data,
            image_format=data.get("image_format", "png"),
            confidence=data.get("confidence", 0.0)
        )
        
        if "caption" in data:
            figure.caption = data["caption"]
        
        if "figure_type" in data:
            figure.figure_type = data["figure_type"]
        
        if "metadata" in data:
            figure.metadata = data["metadata"]
        
        return figure


class FigurePredictor:
    """
    Figure detection and extraction using Docling's native capabilities.
    
    This class leverages Docling's figure detection and extraction models
    to identify figures in documents and extract their content.
    """
    
    def __init__(
        self,
        figure_confidence_threshold: float = 0.5,
        enable_figure_classification: bool = True,
        enable_caption_detection: bool = True,
        rasterizer: Optional[PDFRasterizer] = None,
        output_dir: Optional[str] = None,
        custom_models_path: Optional[str] = None,
        deduplicate_figures: bool = True,
        **kwargs
    ):
        """
        Initialize the figure predictor with configuration options.
        
        Args:
            figure_confidence_threshold: Minimum confidence for figure detection
            enable_figure_classification: Whether to classify figure types
            enable_caption_detection: Whether to detect and link figure captions
            rasterizer: Optional PDFRasterizer instance for page image generation
            output_dir: Directory to save extracted figures
            custom_models_path: Path to custom figure models (if any)
            deduplicate_figures: Whether to deduplicate identical figures
            **kwargs: Additional configuration options
        """
        self.figure_confidence_threshold = figure_confidence_threshold
        self.enable_figure_classification = enable_figure_classification
        self.enable_caption_detection = enable_caption_detection
        self.output_dir = output_dir
        self.custom_models_path = custom_models_path
        self.deduplicate_figures = deduplicate_figures
        self.config = kwargs
        
        # Get or create rasterizer
        self.rasterizer = rasterizer or get_pdf_rasterizer()
        
        # Create output directory if specified
        if self.output_dir:
            os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(
            f"Initializing FigurePredictor (confidence threshold: {figure_confidence_threshold}, "
            f"figure classification: {enable_figure_classification}, "
            f"caption detection: {enable_caption_detection})"
        )
        
        # Initialize figure models if available
        self.figure_model = None
        
        if HAS_FIGURE_MODELS:
            try:
                # Initialize document picture classifier
                self.figure_model = DocumentPictureClassifier(
                    confidence_threshold=figure_confidence_threshold,
                    model_path=custom_models_path,
                    **kwargs
                )
                logger.info("Successfully initialized Docling DocumentPictureClassifier")
            except Exception as e:
                logger.error(f"Failed to initialize Docling DocumentPictureClassifier: {e}")
                self.figure_model = None
        else:
            logger.warning(
                "Docling figure models not available. "
                "Using basic figure extraction with limited capabilities."
            )
    
    def predict(
        self, 
        document: Union[PdfDocument, str, Path, BinaryIO],
        **kwargs
    ) -> List[FigureItem]:
        """
        Detect figures in a document and extract their content.
        
        Args:
            document: PdfDocument, path to PDF file, or file-like object
            **kwargs: Additional processing options
            
        Returns:
            List of FigureItem objects representing detected figures
        """
        logger.info("Starting figure detection and extraction")
        
        figures = []
        figure_hashes = set()  # For deduplication
        
        # Use Docling's figure model if available
        if self.figure_model and HAS_FIGURE_MODELS:
            try:
                # Process document using Docling's figure model
                detected_figures = self.figure_model.detect_pictures(document)
                
                # Convert Docling figure representations to FigureItems
                for figure_idx, figure_data in enumerate(detected_figures):
                    figure_item = self._convert_docling_figure(figure_data, figure_idx)
                    
                    if not figure_item:
                        continue
                    
                    # Deduplicate if enabled
                    if self.deduplicate_figures:
                        figure_hash = figure_item.get_hash()
                        if figure_hash and figure_hash in figure_hashes:
                            logger.debug(f"Skipping duplicate figure on page {figure_item.page_idx}")
                            continue
                        figure_hashes.add(figure_hash)
                    
                    figures.append(figure_item)
                
                logger.info(f"Detected {len(figures)} figures using Docling's DocumentPictureClassifier")
                return figures
            except Exception as e:
                logger.warning(f"Error using Docling figure model: {e}. Falling back to basic extraction.")
        
        # Fallback to basic figure extraction
        try:
            # Open PDF document if needed
            pdf_doc = self._get_pdf_document(document)
            
            # Extract figures using basic methods
            figures = self._extract_figures_basic(pdf_doc)
            
            logger.info(f"Extracted {len(figures)} figures using basic extraction")
            return figures
        except Exception as e:
            logger.error(f"Error extracting figures: {e}")
            return []
    
    def _convert_docling_figure(self, figure_data: Dict[str, Any], figure_idx: int) -> Optional[FigureItem]:
        """
        Convert Docling figure representation to a FigureItem.
        
        Args:
            figure_data: Docling figure data
            figure_idx: Index of the figure
            
        Returns:
            FigureItem or None if conversion fails
        """
        try:
            # Extract basic figure metadata
            page_idx = figure_data.get("page_num", 0) - 1  # Convert 1-based to 0-based
            bbox = figure_data.get("bbox", (0, 0, 0, 0))
            confidence = figure_data.get("confidence", 0.0)
            
            # Get image data
            image_data = figure_data.get("image_data", None)
            image_format = figure_data.get("format", "png")
            
            # Create FigureItem
            figure_item = FigureItem(
                page_idx=page_idx,
                figure_idx=figure_idx,
                bbox=bbox,
                image_data=image_data,
                image_format=image_format,
                confidence=confidence
            )
            
            # Set figure type if classification is enabled
            if self.enable_figure_classification and "figure_type" in figure_data:
                figure_item.set_figure_type(figure_data["figure_type"])
            
            # Extract caption if available
            if self.enable_caption_detection and "caption" in figure_data:
                caption_text = figure_data["caption"].get("text", "")
                caption_bbox = figure_data["caption"].get("bbox", None)
                figure_item.set_caption(caption_text, caption_bbox)
            
            # Add any additional metadata
            if "metadata" in figure_data:
                figure_item.metadata = figure_data["metadata"]
            
            # Save figure to output directory if specified
            if self.output_dir and figure_item.image_data:
                filename = f"figure_{page_idx+1:03d}_{figure_idx+1:03d}.{figure_item.image_format}"
                output_path = os.path.join(self.output_dir, filename)
                if figure_item.save_image(output_path):
                    figure_item.metadata["saved_path"] = output_path
            
            return figure_item
        except Exception as e:
            logger.error(f"Error converting Docling figure: {e}")
            return None
    
    def _get_pdf_document(self, document: Union[PdfDocument, str, Path, BinaryIO]) -> PdfDocument:
        """
        Get a PdfDocument from various input types.
        
        Args:
            document: PdfDocument, path to PDF file, or file-like object
            
        Returns:
            PdfDocument instance
        """
        from docling_parse.pdf_parser import DoclingPdfParser
        
        if isinstance(document, PdfDocument):
            return document
        
        # Parse the document
        parser = DoclingPdfParser()
        
        if isinstance(document, (str, Path)):
            # Path to PDF file
            return parser.load(path_or_stream=str(document))
        elif hasattr(document, 'read'):
            # File-like object
            return parser.load(path_or_stream=document)
        else:
            raise ValueError(f"Unsupported document type: {type(document)}")
    
    def _extract_figures_basic(self, pdf_doc: PdfDocument) -> List[FigureItem]:
        """
        Extract figures using basic methods when Docling models are not available.
        
        Args:
            pdf_doc: PdfDocument to analyze
            
        Returns:
            List of FigureItem objects representing extracted figures
        """
        figures = []
        figure_hashes = set()  # For deduplication
        
        # Process each page in the document
        for page_idx, page in enumerate(pdf_doc.pages):
            # Extract embedded images if available
            if hasattr(page, 'images'):
                for img_idx, img in enumerate(page.images):
                    # Create figure item from embedded image
                    figure_item = self._create_figure_from_image(img, page_idx, img_idx)
                    
                    if not figure_item:
                        continue
                    
                    # Deduplicate if enabled
                    if self.deduplicate_figures:
                        figure_hash = figure_item.get_hash()
                        if figure_hash and figure_hash in figure_hashes:
                            logger.debug(f"Skipping duplicate figure on page {page_idx+1}")
                            continue
                        figure_hashes.add(figure_hash)
                    
                    # Look for caption
                    if self.enable_caption_detection:
                        caption = self._find_caption_basic(page, figure_item.bbox)
                        if caption:
                            figure_item.set_caption(caption.get("text", ""), caption.get("bbox", None))
                    
                    figures.append(figure_item)
            else:
                # If no embedded images, rasterize the page and look for figure-like regions
                logger.debug(f"No embedded images found on page {page_idx+1}, using rasterization")
                
                # Rasterize the page
                img, metadata = self.rasterizer.rasterize_page(pdf_doc, page_idx)
                
                if img:
                    # Try to find figure regions in the rasterized page
                    regions = self._find_figure_regions(img, page_idx)
                    
                    for region_idx, region in enumerate(regions):
                        # Extract region from the image
                        region_img = img.crop(region["bbox_pixels"])
                        
                        # Convert to bytes
                        img_bytes = io.BytesIO()
                        region_img.save(img_bytes, format="PNG")
                        img_data = img_bytes.getvalue()
                        
                        # Create figure item
                        figure_item = FigureItem(
                            page_idx=page_idx,
                            figure_idx=region_idx,
                            bbox=region["bbox_pdf"],
                            image_data=img_data,
                            image_format="png",
                            confidence=0.5  # Low confidence for heuristic detection
                        )
                        
                        # Deduplicate if enabled
                        if self.deduplicate_figures:
                            figure_hash = figure_item.get_hash()
                            if figure_hash and figure_hash in figure_hashes:
                                continue
                            figure_hashes.add(figure_hash)
                        
                        # Look for caption
                        if self.enable_caption_detection:
                            caption = self._find_caption_basic(page, figure_item.bbox)
                            if caption:
                                figure_item.set_caption(caption.get("text", ""), caption.get("bbox", None))
                        
                        # Save figure to output directory if specified
                        if self.output_dir:
                            filename = f"figure_{page_idx+1:03d}_{region_idx+1:03d}.png"
                            output_path = os.path.join(self.output_dir, filename)
                            if figure_item.save_image(output_path):
                                figure_item.metadata["saved_path"] = output_path
                        
                        figures.append(figure_item)
        
        return figures
    
    def _create_figure_from_image(
        self, 
        image: ImageRef, 
        page_idx: int, 
        img_idx: int
    ) -> Optional[FigureItem]:
        """
        Create a FigureItem from a Docling ImageRef.
        
        Args:
            image: Docling ImageRed
            page_idx: Page index
            img_idx: Image index
            
        Returns:
            FigureItem or None if creation fails
        """
        try:
            # Extract image data and properties
            image_data = image.data if hasattr(image, 'data') else None
            bbox = image.bbox if hasattr(image, 'bbox') else (0, 0, 0, 0)
            
            # Determine image format
            image_format = "png"  # Default
            if hasattr(image, 'format'):
                image_format = image.format.lower()
            
            # Create figure item
            figure_item = FigureItem(
                page_idx=page_idx,
                figure_idx=img_idx,
                bbox=bbox,
                image_data=image_data,
                image_format=image_format,
                confidence=0.8  # Higher confidence for embedded images
            )
            
            # Save figure to output directory if specified
            if self.output_dir and image_data:
                filename = f"figure_{page_idx+1:03d}_{img_idx+1:03d}.{image_format}"
                output_path = os.path.join(self.output_dir, filename)
                if figure_item.save_image(output_path):
                    figure_item.metadata["saved_path"] = output_path
            
            return figure_item
        except Exception as e:
            logger.error(f"Error creating figure from image: {e}")
            return None
    
    def _find_figure_regions(self, img: Image.Image, page_idx: int) -> List[Dict[str, Any]]:
        """
        Find figure-like regions in a rasterized page.
        
        Args:
            img: Rasterized page image
            page_idx: Page index
            
        Returns:
            List of dictionaries describing figure regions
        """
        if not HAS_PIL:
            return []
        
        regions = []
        
        # This is a placeholder for more sophisticated region detection
        # In a real implementation, you would use image analysis to find figure-like regions
        
        # For now, just consider the whole page as one region
        region = {
            "bbox_pixels": (0, 0, img.width, img.height),
            "bbox_pdf": self.rasterizer.map_image_to_pdf_coordinates(
                (0, 0, img.width, img.height), page_idx, None
            )
        }
        regions.append(region)
        
        return regions
    
    def _find_caption_basic(self, page: Page, figure_bbox: Tuple[float, float, float, float]) -> Optional[Dict[str, Any]]:
        """
        Find a figure caption near a detected figure.
        
        Args:
            page: Page containing the figure
            figure_bbox: Bounding box of the figure
            
        Returns:
            Caption dictionary or None if no caption found
        """
        if not hasattr(page, 'lines') or not page.lines:
            return None
        
        # Extract figure coordinates
        x0, y0, x1, y1 = figure_bbox
        
        # Look for captions below the figure
        closest_caption = None
        min_distance = float('inf')
        
        for line in page.lines:
            text = line.text.strip().lower()
            
            # Check if line might be a caption (starts with "figure" or "fig.")
            if text.startswith(('figure ', 'fig.', 'image ')):
                # Check if line is below the figure
                if hasattr(line, 'bbox'):
                    line_x0, line_y0, line_x1, line_y1 = line.bbox
                    
                    # Caption should be below the figure and horizontally aligned
                    if line_y0 > y1 and (line_x0 < x1 and line_x1 > x0):
                        # Calculate vertical distance
                        distance = line_y0 - y1
                        
                        # Update closest caption
                        if distance < min_distance:
                            min_distance = distance
                            closest_caption = {
                                "text": line.text,
                                "bbox": line.bbox
                            }
        
        return closest_caption


# Singleton instance for global use
_figure_predictor = None


def get_figure_predictor(
    figure_confidence_threshold: float = 0.5,
    enable_figure_classification: bool = True,
    enable_caption_detection: bool = True,
    **kwargs
) -> FigurePredictor:
    """
    Get or create a singleton instance of FigurePredictor.
    
    Args:
        figure_confidence_threshold: Minimum confidence for figure detection
        enable_figure_classification: Whether to classify figure types
        enable_caption_detection: Whether to detect and link figure captions
        **kwargs: Additional configuration options
        
    Returns:
        Singleton instance of FigurePredictor
    """
    global _figure_predictor
    if _figure_predictor is None:
        _figure_predictor = FigurePredictor(
            figure_confidence_threshold=figure_confidence_threshold,
            enable_figure_classification=enable_figure_classification,
            enable_caption_detection=enable_caption_detection,
            **kwargs
        )
    return _figure_predictor 