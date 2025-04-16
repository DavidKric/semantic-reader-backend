# Testing Framework for Semantic-Reader-Backend

This directory contains the comprehensive test suite for the Semantic-Reader-Backend. The tests validate every aspect of the document processing pipeline, API endpoints, and the integration with Docling.

## Directory Structure

The tests are organized by feature area:

```
tests/
├── api/                # API endpoint tests
├── converter/          # Converter module tests
├── data/               # Test PDF files and expected outputs
│   └── expected/       # Expected JSON outputs (snapshots)
├── figures/            # Figure detection and extraction tests
├── layout/             # Layout analysis and reading order tests
├── ocr/                # OCR text extraction tests
├── tables/             # Table extraction and structure tests
└── visuals/            # Generated visualization images
```

## Running Tests

### Running the Full Test Suite

To run the entire test suite with coverage report and HTML output:

```bash
pytest --cov=app --html=reports/test_report.html --self-contained-html
```

This will:
- Run all tests
- Generate a coverage report
- Create an HTML report with visualizations in `reports/test_report.html`

### Running Specific Tests

To run tests for a specific feature area:

```bash
# Run only layout tests
pytest tests/layout/

# Run a specific test file
pytest tests/tables/test_extraction.py

# Run a specific test function
pytest tests/api/test_routes.py::test_conversion_endpoint_success
```

## Test Visualization

Many tests generate visual artifacts in the `tests/visuals/` directory:

- `*_layout.png` - Text layout and bounding boxes
- `*_tables.png` - Table detection and structure
- `*_figures.png` - Figure detection and captions
- `*_ocr.png` - OCR text extraction

These images are also embedded in the HTML report for easy inspection.

## Updating Expected Outputs (Snapshots)

When intentional changes are made to the output format, the expected JSON files (snapshots) need to be updated:

1. Run the specific failing test to identify the differences:
   ```bash
   pytest tests/converter/test_full_conversion.py -v
   ```

2. Verify that the differences are expected and acceptable.

3. To update a specific expected output:
   ```bash
   # Manually copy the current output to the expected directory
   cp /path/to/current/output.json tests/data/expected/sample_name.json
   ```

4. To update all expected outputs:
   ```bash
   # Run the update script (to be implemented)
   python tests/update_expected_outputs.py
   ```

5. Run the tests again to ensure they pass with the updated outputs.

## Adding New Tests

When adding new tests:

1. Place them in the appropriate feature directory.
2. Follow the naming convention: `test_<feature>.py`.
3. Use the fixtures from `conftest.py` for common operations.
4. For visualization tests, use the `attach_visual` fixture to include images in the report.
5. For JSON comparisons, use the `compare_json` fixture to compare with expected outputs.

## Test Data

Sample PDF files in `tests/data/` are used as inputs for the tests:

- `sample1_simple.pdf` - Simple text-only document
- `sample2_multicolumn.pdf` - Multi-column document
- `sample3_scanned.pdf` - Scanned document for OCR testing
- `sample4_tables.pdf` - Document with tables
- `sample5_figures.pdf` - Document with figures
- `sample6_mixed.pdf` - Complex document with mixed content
- `corrupt.pdf` - Invalid PDF for error handling tests

Each sample has a corresponding expected JSON output in `tests/data/expected/`.

## Coverage Goals

The test suite aims for 100% test coverage of:

- Document processing features (layout, OCR, tables, figures)
- API routes
- Converter module
- Error handling and edge cases

Coverage reports can be viewed in the terminal after running tests or as an HTML report:

```bash
# Generate HTML coverage report
coverage html
# Open htmlcov/index.html in a browser
``` 