# PaperMage Docling

A document processing library that uses Docling directly for robust document understanding.

## Architecture

This library provides a simplified interface to Docling's powerful document processing capabilities. After the recent refactoring, the library now uses Docling's native functionality directly without any intermediate layers.

### Key Components

- `convert_document`: Central function that directly uses Docling's DocumentConverter to process documents
- Uses DoclingParse v4 for optimal processing, including robust RTL support

## Usage

### Basic Document Processing

```python
from papermage_docling import convert_document

# Process a document with default settings
result = convert_document("document.pdf")

# Process with custom options
result = convert_document(
    source="document.pdf",
    options={
        "enable_ocr": True,
        "ocr_language": "eng",
        "detect_rtl": True,
        "detect_tables": True,
        "detect_figures": True
    }
)

# Access document metadata
language = result.get("metadata", {}).get("language", "en")
is_rtl = result.get("metadata", {}).get("is_rtl_language", False)

print(f"Document language: {language}, RTL: {is_rtl}")

# Access document content
full_text = result.get("full_text", "")
pages = result.get("pages", [])
tables = result.get("entities", {}).get("tables", [])
figures = result.get("entities", {}).get("figures", [])
```

### Processing Files from Different Sources

```python
# From a file path
result = convert_document("document.pdf")

# From bytes
with open("document.pdf", "rb") as f:
    pdf_bytes = f.read()
    result = convert_document(pdf_bytes)

# From a file object
with open("document.pdf", "rb") as f:
    result = convert_document(f)
```

## Features

- Full integration with Docling's document processing pipeline
- Uses DoclingParse v4 for optimal processing
- Built-in RTL detection and processing
- Language detection for documents
- Table and figure extraction
- OCR support for scanned documents

## Installation

```bash
# Using pip
pip install papermage-docling

# Using uv (recommended)
uv pip install papermage-docling
```

## Requirements

- Python 3.8+
- `docling` and related packages

## License

MIT
