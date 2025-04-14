from typing import Dict, Union, Optional, Any, List
import logging
from pathlib import Path
import os
import io

# Import Docling document structures
try:
    from docling_parse.pdf_parser import DoclingPdfParser as DoclingPdfParserBase
    from docling_parse.pdf_parser import PdfDocument
    from docling_core.types import DoclingDocument
except ImportError:
    logging.warning("Docling dependencies not found. PDF parsing functionality will not work.")
    # Define stub classes for type hints
    class DoclingPdfParserBase:
        def __init__(self, *args, **kwargs):
            pass
        
        def load(self, path_or_stream, **kwargs):
            pass
    
    class PdfDocument:
        pass
    
    class DoclingDocument:
        pass

# Import converter
from papermage_docling.converters import DoclingToPaperMageConverter

# Import RTL utilities
from papermage_docling.predictors.rtl_utils import (
    contains_rtl_characters, detect_rtl_text, apply_rtl_processing, 
    segment_rtl_sections, get_rtl_direction_marker
)

# Import language prediction
from papermage_docling.predictors.language_predictor import (
    LanguagePredictor, is_rtl_language
)

logger = logging.getLogger(__name__)


class DoclingPdfParser:
    """
    PDF parser that uses Docling's native data structures for internal processing
    and optionally converts to PaperMage format at the output level.
    
    This parser wraps docling-parse functionality and maintains Docling's
    native structures throughout the processing pipeline, with optional conversion
    to PaperMage format only when requested at the output stage.
    """
    
    def __init__(
        self,
        enable_ocr: bool = False,
        ocr_language: str = "eng",
        detect_rtl: bool = True,
        enable_language_detection: bool = True,
        language_detection_method: str = 'auto',
        **kwargs
    ):
        """
        Initialize the parser with configuration options.
        
        Args:
            enable_ocr: Whether to enable OCR for scanned documents
            ocr_language: Language code for OCR (e.g., 'eng', 'heb')
            detect_rtl: Whether to enable RTL text detection and processing
            enable_language_detection: Whether to enable language detection
            language_detection_method: Method for language detection ('auto', 'langdetect', 'fasttext')
            **kwargs: Additional configuration options to pass to Docling's parser
        """
        self.enable_ocr = enable_ocr
        self.ocr_language = ocr_language
        self.detect_rtl = detect_rtl
        self.enable_language_detection = enable_language_detection
        self.language_detection_method = language_detection_method
        self.config = kwargs
        
        logger.info(
            f"Initializing DoclingPdfParser (OCR: {enable_ocr}, "
            f"OCR language: {ocr_language}, RTL detection: {detect_rtl}, "
            f"Language detection: {enable_language_detection})"
        )

        # Initialize language predictor if enabled
        if self.enable_language_detection:
            self.language_predictor = LanguagePredictor(
                detect_rtl=self.detect_rtl, 
                method=self.language_detection_method
            )
            logger.info("Language detection initialized")
        else:
            self.language_predictor = None
        
        # Initialize Docling's parser
        try:
            self.pdf_parser = DoclingPdfParserBase(
                enable_ocr=enable_ocr,
                ocr_language=ocr_language,
                **kwargs
            )
            logger.info("Successfully initialized Docling PDF parser")
        except Exception as e:
            logger.error(f"Failed to initialize Docling PDF parser: {e}")
            raise
    
    def _validate_pdf_path(self, pdf_path: Union[str, Path, io.BytesIO]) -> Union[str, io.BytesIO]:
        """
        Validate and normalize the PDF path or stream.
        
        Args:
            pdf_path: Path to the PDF file or a BytesIO object
            
        Returns:
            Normalized path as string or BytesIO object
            
        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            ValueError: If the input is invalid
        """
        if isinstance(pdf_path, io.BytesIO):
            return pdf_path
        
        if isinstance(pdf_path, (str, Path)):
            path_str = str(pdf_path)
            if not os.path.exists(path_str):
                raise FileNotFoundError(f"PDF file not found: {path_str}")
            return path_str
        
        raise ValueError(f"Invalid PDF path or stream: {pdf_path}")
    
    def parse(self, pdf_path: Union[str, Path, io.BytesIO], output_format: str = 'docling', **kwargs) -> Union[PdfDocument, Any]:
        """
        Parse a PDF document and return it in the specified format.
        
        This method uses Docling's native data structures for all internal processing,
        and only converts to PaperMage format at the output level if requested.
        
        Args:
            pdf_path: Path to the PDF file or a BytesIO object containing PDF data
            output_format: Format of the returned document. Options:
                - 'docling' (default): Return Docling's native PdfDocument
                - 'papermage': Convert to PaperMage's Document format
            **kwargs: Additional parsing options
            
        Returns:
            If output_format is 'docling', returns a PdfDocument
            If output_format is 'papermage', returns a PaperMage Document
            
        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            ValueError: If output_format is invalid
            
        Examples:
            # Parse a PDF and work with Docling's native structures (recommended for internal processing)
            pdf_doc = parser.parse('example.pdf')  # Default is docling format
            for page in pdf_doc.pages:
                for line in page.lines:
                    print(line.text)
            
            # Parse a PDF and convert to PaperMage format (for API/output compatibility)
            papermage_doc = parser.parse('example.pdf', output_format='papermage')
            print(papermage_doc.symbols)  # Full text
            for entity in papermage_doc.get_entity_layer('sentences'):
                print(entity.text)
        """
        logger.info(f"Parsing PDF: {pdf_path} (output_format: {output_format})")
        
        # Validate PDF path or stream
        validated_pdf_path = self._validate_pdf_path(pdf_path)
        
        # Parse the PDF using Docling's native parser
        try:
            logger.info("Processing PDF with Docling's native parser...")
            pdf_doc = self.pdf_parser.load(path_or_stream=validated_pdf_path, **kwargs)
            logger.info(f"Successfully parsed PDF with {len(pdf_doc.pages)} pages")
        except Exception as e:
            logger.error(f"Failed to parse PDF: {e}")
            raise
        
        # Initialize or ensure metadata exists
        if not hasattr(pdf_doc, 'metadata'):
            pdf_doc.metadata = {}
        
        # Detect primary document language if enabled
        if self.enable_language_detection and self.language_predictor:
            try:
                logger.info("Detecting document language...")
                # Extract text for language detection
                document_text = self._extract_document_text(pdf_doc)
                
                # Detect language
                language_info = self.language_predictor.predict_document_language(document_text)
                
                # Store language information in metadata
                pdf_doc.metadata['language'] = language_info['language']
                pdf_doc.metadata['language_name'] = language_info['language_name']
                pdf_doc.metadata['language_confidence'] = language_info['confidence']
                pdf_doc.metadata['is_rtl_language'] = language_info['is_rtl']
                
                # Store additional language information if present
                if language_info['additional_languages']:
                    pdf_doc.metadata['additional_languages'] = language_info['additional_languages']
                
                # Auto-enable RTL processing if language is RTL
                if self.detect_rtl and language_info['is_rtl']:
                    logger.info(f"Detected RTL language: {language_info['language_name']}")
                    pdf_doc.metadata['rtl_processing_required'] = True
                
                logger.info(f"Language detection complete: {language_info['language_name']} "
                            f"(confidence: {language_info['confidence']:.2f})")
            except Exception as e:
                logger.warning(f"Language detection failed: {e}. Continuing with processing.")
        
        # Apply RTL processing if enabled
        if self.detect_rtl:
            try:
                logger.info("Applying RTL text processing on Docling's native structures...")
                self._process_rtl_text(pdf_doc, pdf_doc.metadata.get('language'))
                logger.info("RTL processing completed")
            except Exception as e:
                logger.warning(f"RTL processing failed: {e}. Continuing with unprocessed text.")
        
        # Return the document in the requested format
        if output_format.lower() == 'docling':
            logger.info("Returning Docling native format")
            return pdf_doc
        elif output_format.lower() == 'papermage':
            logger.info("Converting to PaperMage format at the output level")
            try:
                papermage_doc = DoclingToPaperMageConverter.convert_pdf_document(pdf_doc)
                logger.info("Successfully converted to PaperMage format")
                return papermage_doc
            except Exception as e:
                logger.error(f"Failed to convert to PaperMage format: {e}")
                raise
        else:
            error_msg = f"Invalid output format: {output_format}. Supported formats: 'docling', 'papermage'"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _extract_document_text(self, pdf_doc: PdfDocument, max_chars: int = 10000) -> str:
        """
        Extract text from document for language detection.
        
        This method extracts a sample of text from throughout the document to
        provide a representative sample for language detection.
        
        Args:
            pdf_doc: Docling's PdfDocument instance
            max_chars: Maximum number of characters to extract
            
        Returns:
            Extracted text sample
        """
        text_parts = []
        total_chars = 0
        
        # If the document has few pages, sample more from each page
        sample_size = min(max_chars // max(1, len(pdf_doc.pages)), 1000)
        
        for page in pdf_doc.pages:
            page_text = []
            
            # Extract text from lines
            for line in page.lines:
                if line.text and line.text.strip():
                    page_text.append(line.text)
                    
                    # If we've collected enough text from this page, stop
                    if len(' '.join(page_text)) >= sample_size:
                        break
            
            # Add page text to overall sample
            if page_text:
                text_parts.append(' '.join(page_text))
                total_chars += len(text_parts[-1])
                
                # If we've collected enough text overall, stop
                if total_chars >= max_chars:
                    break
        
        return ' '.join(text_parts)
    
    def _process_rtl_text(self, doc, document_language=None):
        """
        Process right-to-left text in the document.
        
        Args:
            doc: The document to process
            document_language: The detected language of the document
            
        Returns:
            The processed document
        """
        if not self.detect_rtl:
            return doc
            
        has_rtl = False
        
        # Check if document language is RTL
        if document_language:
            doc.metadata["language"] = document_language
            
        # Process each page
        for page in doc.pages:
            # Process each paragraph
            for paragraph in page.paragraphs:
                if not paragraph.text:
                    continue
                    
                # Detect if paragraph contains RTL text
                is_rtl_paragraph = detect_rtl_text(paragraph.text)
                
                if is_rtl_paragraph:
                    has_rtl = True
                    
                    # Get RTL direction marker for the paragraph
                    rtl_marker = get_rtl_direction_marker(paragraph.text)
                    
                    # Apply RTL processing to the paragraph text
                    processed_text = apply_rtl_processing(paragraph.text)
                    paragraph.text = processed_text
                    
                    # Segment RTL sections if it contains mixed text
                    rtl_segments = segment_rtl_sections(paragraph.text)
                    if len(rtl_segments) > 1:
                        paragraph.metadata["rtl_segments"] = rtl_segments
                    
                    # Set RTL metadata
                    paragraph.metadata["is_rtl"] = True
                    paragraph.metadata["rtl_marker"] = rtl_marker
        
        # Update document metadata
        if has_rtl:
            doc.metadata["has_rtl"] = True
            
        return doc 