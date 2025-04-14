# PaperMage Docling

A document processing library that combines the strengths of PaperMage and Docling for robust document understanding.

## Architecture

### Core Architecture

This library uses `DoclingDocument` from `docling_core.types` as the central data structure throughout the entire processing pipeline. This ensures consistent data representation and eliminates unnecessary format conversions between processing steps.

Format conversions (e.g., to/from PaperMage format) occur **only at API boundaries**, maintaining DoclingDocument as the native format for all internal operations.

![Architecture Diagram](docs/images/architecture.png)

### Key Components

#### Document Storage

- `DocumentStorage`: Abstract interface for document persistence
- `FileDocumentStorage`: Implementation that stores documents as compressed JSON files
- Optimized for DoclingDocument structure with metadata extraction and indexing

#### Document Caching

- `DocumentCache`: Abstract interface for document caching
- `LRUDocumentCache`: Implementation using a Least Recently Used caching strategy
- Thread-safe with time-to-live (TTL) support

#### Processing Pipeline

- `Pipeline`: Modular document processing pipeline with error handling and retries
- `DocumentProcessor`: Interface for pipeline processing steps
- `SimplePipeline`: Higher-level pipeline with common document processing steps

#### API Service

- `DoclingApiService`: High-level API for document processing
- Handles format conversions at API boundaries
- Provides methods for document processing, storage, and retrieval

### Data Flow

1. **Input**: Documents enter the system at API boundaries (either as files or PaperMage format)
2. **Conversion**: If needed, documents are converted to DoclingDocument at the boundary
3. **Processing**: Documents flow through the pipeline as DoclingDocument instances
4. **Storage**: Processed documents are stored in their native DoclingDocument format
5. **Output**: Documents are converted to the requested format only at API boundaries

## Usage

### Basic Document Processing

```python
from papermage_docling.api_service import get_api_service

# Get API service
api = get_api_service()

# Process a document
doc_id = api.process_document("document.pdf", return_id=True)

# Retrieve the document
doc = api.get_document(doc_id)

# Or retrieve as PaperMage format
pm_doc = api.get_document(doc_id, as_papermage=True)
```

### Building Custom Pipelines

```python
from papermage_docling.pipeline import SimplePipeline
from papermage_docling.predictors import get_table_predictor, get_figure_predictor

# Create a pipeline
pipeline = SimplePipeline("CustomPipeline")

# Add processing steps
pipeline.add_processor(get_table_predictor())
pipeline.add_processor(get_figure_predictor())

# Process a document
doc = pipeline.process_file("document.pdf")
```

### Using Storage and Cache

```python
from papermage_docling.storage import FileDocumentStorage, LRUDocumentCache

# Create storage
storage = FileDocumentStorage("documents")

# Create cache
cache = LRUDocumentCache(max_size=100)

# Save a document
doc_id = storage.save(doc)

# Load a document with caching
cached_doc = cache.get(doc_id)
if cached_doc is None:
    doc = storage.load(doc_id)
    cache.put(doc_id, doc)
else:
    doc = cached_doc
```

## Development

### Adding a New Predictor

1. Create a new predictor class that extends `DocumentProcessor`
2. Implement the `process` method that accepts and returns a `DoclingDocument`
3. Register the predictor with the pipeline

```python
from papermage_docling.pipeline import DocumentProcessor

class MyPredictor(DocumentProcessor):
    def __init__(self):
        super().__init__("MyPredictor")
    
    def process(self, doc, **kwargs):
        # Process the document
        return doc
```

### Adding a New Storage Backend

1. Create a new class that implements the `DocumentStorage` interface
2. Implement all required methods (save, load, delete, etc.)
3. Use the new storage in API service or custom code

## Features

- PDF parsing and extraction using Docling's document structures
- Seamless conversion to PaperMage format
- Built-in RTL text detection and processing
- Language detection for document and text segments
- Optional OCR support for scanned documents

## Installation

### Basic Installation

```bash
pip install papermage-docling
```

### Installation with RTL Support

For full RTL support and enhanced language detection:

```bash
pip install "papermage-docling[rtl]"
```

## Usage

### Basic PDF Parsing

```python
from papermage_docling.parsers import DoclingPdfParser

# Initialize with RTL detection enabled
parser = DoclingPdfParser(
    enable_ocr=False,  # Set to True to enable OCR
    detect_rtl=True,   # Enable RTL processing
    enable_language_detection=True  # Enable language detection
)

# Parse PDF in Docling format (for internal processing)
pdf_doc = parser.parse('example.pdf')  # Default is 'docling' format

# Get detected language information
language = pdf_doc.metadata.get('language', 'unknown')
language_name = pdf_doc.metadata.get('language_name', 'Unknown')
is_rtl = pdf_doc.metadata.get('is_rtl_language', False)

print(f"Document language: {language_name} (code: {language}, RTL: {is_rtl})")

# Process each page and line
for page in pdf_doc.pages:
    for line in page.lines:
        # Line text is already processed for RTL if needed
        print(line.text)
```

### Converting to PaperMage Format

```python
# Parse PDF and convert to PaperMage format
papermage_doc = parser.parse('example.pdf', output_format='papermage')

# Access text through PaperMage structures
full_text = papermage_doc.symbols
print(f"Full document text: {full_text[:100]}...")  # Print first 100 chars

# Access extracted entities
for entity in papermage_doc.get_entity_layer('sentences'):
    print(entity.text)
```

## RTL Language Support

The library provides comprehensive support for right-to-left (RTL) languages including:

- Arabic
- Hebrew
- Persian
- Urdu
- Other RTL languages

RTL text processing includes:

- RTL text detection
- Character and word reordering
- Mixed-direction text processing
- Unicode normalization

## Language Detection

Language detection features allow the library to:

- Automatically detect document language
- Handle multi-language documents
- Identify RTL languages
- Provide language confidence scores

Language detection is implemented using:

1. `langdetect` (default) - Lightweight language detection
2. `fasttext` (optional) - More advanced, high-accuracy detection

## Advanced Configuration

```python
# Advanced configuration options
parser = DoclingPdfParser(
    # Basic options
    enable_ocr=True,
    ocr_language="heb",  # OCR language code (e.g., "eng", "heb", "ara")
    detect_rtl=True,
    
    # Language detection options
    enable_language_detection=True,
    language_detection_method="fasttext",  # "auto", "langdetect", or "fasttext"
    
    # Additional Docling parser options
    pdf_password="optional-password",
    extract_tables=True
)
```

## Requirements

- Python 3.8+
- `docling-core`, `docling` and `docling-parse`
- `arabic-reshaper` and `python-bidi` for RTL support
- `langdetect` for language detection
- Optional: `fasttext` for improved language detection

## License

MIT
