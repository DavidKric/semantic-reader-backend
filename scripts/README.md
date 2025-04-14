# Scripts Directory

This directory contains various scripts for development, testing, and project management.

## Directory Structure

```
scripts/
├── dev/                 # Development workflow scripts
│   ├── setup_dev.sh     # Sets up the development environment
│   ├── quality_check.sh # Runs code quality checks
│   └── migrate_to_uv.sh # Migration script for UV dependency management
├── ci/                  # CI/CD related scripts
│   └── run_tests.sh     # Runs pytest with appropriate settings
├── utils/               # Utility scripts
│   ├── analyze_conversions.py # Analyzes document conversion data
│   └── dev.js           # JavaScript development utilities
└── task-master/         # Task-master specific files
    ├── prd.txt          # Product Requirements Document
    ├── prd.md           # Markdown version of PRD
    └── example_prd.txt  # Example PRD template
```

## Usage

### Development Scripts

```bash
# Set up development environment
./scripts/dev/setup_dev.sh

# Run code quality checks
./scripts/dev/quality_check.sh

# Migrate to UV package manager
./scripts/dev/migrate_to_uv.sh
```

### CI Scripts

```bash
# Run tests
./scripts/ci/run_tests.sh
```

### Utility Scripts

```bash
# Analyze document conversions
./scripts/utils/analyze_conversions.py
```

### Task-Master

Task-master files are used for project management and task tracking. The main files are:

- `prd.txt` - The Product Requirements Document used by task-master
- `task-complexity-report.json` - Analysis of task complexity

To parse the PRD and generate tasks:

```bash
task-master parse-prd --input=scripts/task-master/prd.txt
```

## Convenience Commands

For easier access, we provide shortcuts in the `bin/` directory:

```bash
# Setup development environment
./bin/setup

# Run tests
./bin/test
```

# PDF Processing Utilities

This directory contains several scripts for working with PDF documents, particularly those with RTL (right-to-left) text content.

## PDF Text Extraction

The `extract_pdf_text.py` script allows you to extract text from PDF files with RTL text detection and language detection.

### Usage

```bash
python scripts/extract_pdf_text.py -i <input-pdf> [options]
```

### Options

- `-i, --input-pdf`: Path to the PDF file to process (required)
- `-o, --output`: Output file path (default: input filename + .txt or .json)
- `-f, --format`: Output format, either 'text' or 'json' (default: text)
- `-p, --page`: Specific page to process, or -1 for all pages (default: -1)
- `--rtl`: Enable RTL text detection and processing
- `--language-detection`: Enable language detection

### Examples

Extract text with RTL detection to a text file:
```bash
python scripts/extract_pdf_text.py -i document.pdf --rtl
```

Extract with language detection to a JSON file:
```bash
python scripts/extract_pdf_text.py -i document.pdf --rtl --language-detection -f json
```

## PDF Visualization

The `visualize_pdf.py` script provides visualization capabilities for PDF documents at different levels (character, word, or line).

### Usage

```bash
python scripts/visualize_pdf.py -i <input-pdf> [options]
```

### Options

- `-i, --input-pdf`: Path to the PDF file to visualize (required)
- `-o, --output-dir`: Directory to save visualizations
- `-c, --category`: Visualization level: 'all', 'char', 'word', 'line' (default: all)
- `-p, --page`: Specific page to visualize, or -1 for all pages (default: -1)
- `-b, --page-boundary`: Page boundary to use: 'crop_box', 'media_box' (default: crop_box)
- `-l, --log-level`: Logging level: 'info', 'warning', 'error', 'fatal' (default: error)
- `--interactive`: Display visualizations interactively
- `--display-text`: Show text in visualizations (instead of bounding boxes)
- `--log-text`: Log extracted text to console
- `--rtl`: Enable RTL text detection and processing
- `--language-detection`: Enable language detection

### Examples

Visualize all levels with RTL detection:
```bash
python scripts/visualize_pdf.py -i document.pdf --rtl -o visualizations
```

Visualize just lines with text display:
```bash
python scripts/visualize_pdf.py -i document.pdf -c line --display-text --interactive
```

## PDF Comparison

The `compare_pdfs.py` script compares multiple PDF files and generates a report, useful for evaluating RTL detection and language detection capabilities.

### Usage

```bash
python scripts/compare_pdfs.py -i <pdf1> <pdf2> [<pdf3> ...] [options]
```

### Options

- `-i, --input-pdfs`: Paths to PDF files to compare (required, 2 or more)
- `-o, --output`: Output JSON file path (default: comparison_results.json)
- `--max-pages`: Maximum number of pages to process per document (default: -1 for all)
- `--rtl`: Enable RTL text detection and processing
- `--language-detection`: Enable language detection

### Examples

Compare two PDFs with RTL and language detection:
```bash
python scripts/compare_pdfs.py -i english.pdf hebrew.pdf --rtl --language-detection
```

Compare multiple PDFs and limit to first 2 pages each:
```bash
python scripts/compare_pdfs.py -i doc1.pdf doc2.pdf doc3.pdf --rtl --max-pages 2
```

## RTL Text Processing Features

These scripts leverage the following RTL text processing capabilities:

1. **RTL Detection**: Identifies right-to-left scripts like Arabic, Hebrew, Farsi, etc.
2. **Language Detection**: Automatically identifies the primary language of documents
3. **RTL-Aware Text Extraction**: Preserves proper text ordering and direction
4. **Visual Representation**: Shows text with proper directional markers

For developers working on multiple languages, these tools help evaluate how well the system handles bidirectional text.
