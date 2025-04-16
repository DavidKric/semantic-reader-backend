# Test Data for Semantic-Reader-Backend

This directory contains sample PDF files and expected outputs for testing the document processing pipeline.

## Sample PDF Files

The following sample PDF files cover different test cases:

- `sample1_simple.pdf`: A simple text-only PDF file for basic text extraction testing.
- `sample2_multicolumn.pdf`: A multi-column PDF (academic paper) for testing reading order and layout analysis.
- `sample3_scanned.pdf`: A scanned PDF for testing OCR text extraction.
- `sample4_tables.pdf`: A PDF with tables for testing table detection and structure extraction.
- `sample5_figures.pdf`: A PDF with figures for testing figure detection and extraction.
- `sample6_mixed.pdf`: A complex PDF with mixed content (text, tables, figures) for integration testing.
- `corrupt.pdf`: An intentionally corrupted PDF for testing error handling.

## Expected Outputs

The `expected/` directory contains JSON files corresponding to each sample PDF. These files represent the expected output from processing the PDFs and are used for snapshot testing.

- `sample1_simple.json`
- `sample2_multicolumn.json`
- `sample3_scanned.json`
- `sample4_tables.json`
- `sample5_figures.json`
- `sample6_mixed.json`

## Scripts

The following scripts are provided for managing test data:

- `download_samples.py`: Downloads the sample PDF files from public sources.
- `generate_expected_outputs.py`: Processes the sample PDFs and generates expected JSON outputs (requires a functioning document processing pipeline).
- `generate_synthetic_outputs.py`: Generates synthetic JSON outputs for testing when the actual document processing is not available or when controlled test data is needed.

## Usage

To download the sample PDFs:

```bash
python download_samples.py
```

To generate synthetic outputs:

```bash
python generate_synthetic_outputs.py  # Use --force to overwrite existing outputs
```

To generate expected outputs from actual processing (if available):

```bash
python generate_expected_outputs.py  # Use --force to overwrite existing outputs
``` 