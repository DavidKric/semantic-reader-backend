# PaperMage-Docling End-to-End Testing

This directory contains end-to-end (E2E) tests for PaperMage-Docling, designed to compare its outputs with the original PaperMage implementation.

## Overview

The E2E testing framework is designed to:

1. Compare PaperMage-Docling outputs with the original PaperMage
2. Validate compatibility and identical behavior
3. Test various document types (simple, complex layouts, RTL, large docs)
4. Generate detailed reports of differences

## Test Structure

- `test_end_to_end.py`: Main test file with fixtures and comparison functions
- `conftest.py`: Pytest configuration with HTML report setup
- `e2e_test_config.json`: Configuration for tolerances and test parameters
- `test_data/`: Directory containing test documents and cache

## Running Tests

To run all E2E tests:

```bash
# From the project root
pytest papermage_docling/tests/test_end_to_end.py -v
```

To run tests for specific document types:

```bash
# Run tests for simple documents only
pytest papermage_docling/tests/test_end_to_end.py -v -m simple

# Run tests for RTL documents only
pytest papermage_docling/tests/test_end_to_end.py -v -m rtl

# Run performance tests only
pytest papermage_docling/tests/test_end_to_end.py -v -m performance
```

## Configuration

The test framework is configured via `e2e_test_config.json`, which allows for:

- Setting tolerance levels for coordinate differences
- Configuring text similarity thresholds
- Specifying test document paths
- Enabling/disabling HTML reports

## Adding Test Documents

1. Place your test documents in the appropriate subdirectory under `test_data/documents/`:
   - `simple/`: Simple single-column documents
   - `complex/`: Multi-column, tables, complex layouts
   - `rtl/`: Right-to-left language documents
   - `large/`: Large documents for performance testing

2. Update the `document_samples` section in `e2e_test_config.json` to include your new documents.

## Test Reports

HTML test reports are automatically generated in `test_results/html/` with timestamps.
These reports include:

- Overview of pass/fail for each test
- Detailed description of any differences found
- Performance metrics
- Visualizations of the document processing outcomes (when available)

## Integration with CI/CD

These tests can be integrated into CI/CD pipelines by:

1. Installing both PaperMage and PaperMage-Docling
2. Running the E2E tests in the pipeline
3. Publishing the HTML report as an artifact

Example GitHub Actions workflow snippet:

```yaml
- name: Run E2E tests
  run: |
    python -m pytest papermage_docling/tests/test_end_to_end.py -v

- name: Upload test report
  uses: actions/upload-artifact@v2
  with:
    name: e2e-test-report
    path: papermage_docling/tests/test_results/html/*.html
``` 