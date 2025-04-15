Perfect. I’ll create a comprehensive Pytest-based testing plan for your project that mirrors the strategies used in Papermage, Docling, and docling-parser. This will include:

- 100% test coverage goals for every feature of the document processing pipeline
- File structure under `tests/<feature>/...` for modular clarity
- FastAPI endpoint testing with integration coverage
- Automatic generation of HTML reports with rich visualizations (e.g. layout, words, figures, tables, etc.), one image per visualizable feature
- Snapshot testing of JSON outputs for regression protection
- Use of real PDFs with expected outputs for ground truth

Give me a moment to draft the full testing plan, directory structure, and test descriptions for each module.

# Testing Strategy for Semantic-Reader-Backend (Docling Integration)

## Overview and Goals

After refactoring the `semantic-reader-backend` to use IBM’s **Docling** library, we need a comprehensive testing strategy to ensure everything works correctly. Our goal is **100% test coverage** across all components, including:

- **Document Processing Features** – Verify layout analysis, OCR text extraction, table recognition, figure detection, and other content extraction (e.g. code blocks, formulas) ([GitHub - docling-project/docling: Get your documents ready for gen AI](https://github.com/docling-project/docling#:~:text=,Markdown%2C%20HTML%2C%20and%20lossless%20JSON)).
- **API Routes (FastAPI)** – Test every FastAPI endpoint (e.g. conversion requests) for correct responses.
- **Converter Module** – The new `docling-papermage` wrapper that converts Docling’s output into the JSON format (previously produced by PaperMage).
- **JSON Schema Compliance** – Ensure the output JSON matches the expected PaperMage format/schema.
- **Error Handling & Edge Cases** – Simulate corrupted files, missing metadata, and other edge scenarios to confirm graceful handling.

This strategy draws inspiration from similar projects (PaperMage and Docling) to maximize reliability and maintainability.

## Inspiration from Related Projects

We incorporate best practices from existing test suites:

- **PaperMage’s Test Suite** – PaperMage included specialized predictors for tables and figures ([](https://aclanthology.org/2023.emnlp-demo.45.pdf#:~:text=papermage%20includes%20several%20ready)). We mirror its tests for **table structure validation** (checking rows, columns, cell content) and **figure extraction** (detecting figure regions and captions). For example, PaperMage’s `BoxPredictor` can return tables and figures from a document ([](https://aclanthology.org/2023.emnlp-demo.45.pdf#:~:text=Table%201%20for%20a%20summary,doc)); our tests will ensure our system likewise correctly identifies and structures these elements.

- **Docling-Parse Visualization Tests** – Docling’s parser provides visual debugging tools for text layout ([GitHub - docling-project/docling-parse: Simple package to extract text with coordinates from programmatic PDFs](https://github.com/docling-project/docling-parse#:~:text=Simple%20package%20to%20extract%20text%2C,extracted%20paths%20and%20bitmap%20resources)). We emulate this by **visualizing layout outputs** (e.g. bounding boxes for words, lines, tables) to verify that the layout model and reading order are correct. This approach, inspired by Docling’s own visualization utility, helps us catch misaligned text or ordering issues that might not be obvious from JSON alone.

- **Docling Snapshot & Integration Tests** – The Docling project emphasizes **lossless JSON export** for documents ([Docling Technical Report - arXiv](https://arxiv.org/html/2408.09869v4#:~:text=Docling%20Technical%20Report%20,Markdown%20and%20HTML%2C%20which)) and uses snapshot tests to ensure consistent outputs across versions. We adopt **snapshot testing** (golden file comparisons) for our end-to-end pipeline: for each sample PDF, we compare the produced JSON to a stored expected JSON. This will alert us to any unintended changes in the conversion logic while allowing intentional updates via controlled snapshot updates.

By leveraging these approaches, our test suite will validate both the *content* (e.g. tables, figures, text) and the *structure* (JSON schema, ordering) of outputs.

## Test Suite Organization

We will organize tests by feature area, with each set of tests focused on one aspect of the backend. The directory structure will reflect these categories (as shown later), for clarity and ease of running subsets of tests. Key test categories include:

### 1. Document Processing Feature Tests

Each document processing capability provided by Docling (and expected by PaperMage output) gets a dedicated test module. We use **real PDF files** in `tests/data/` as input for these tests, ensuring realistic content. For each feature, we verify both the **raw extraction** and the **structured JSON output**:

- **Layout and Reading Order** (`tests/layout/test_lines.py`): Use PDFs with complex layouts (multi-column, multi-page) to ensure that paragraphs and lines are extracted in correct reading order. For example, given a two-column research paper page, the sequence of text in the JSON should follow the human reading order. The test will parse a sample PDF, then assert that:
  - The number of pages, lines per page, and paragraphs match expectations.
  - A known paragraph of text appears intact and in order in the output JSON.
  - If available, compare the concatenated text output to an expected plain-text (to validate ordering).
  - **Visualization**: generate an image (saved to `tests/visuals/` as e.g. `sample1_layout.png`) drawing bounding boxes around text lines in their reading order (e.g. numbering each line). This helps manually verify that lines were detected and ordered properly.

- **OCR Text Extraction** (`tests/ocr/test_ocr_extraction.py`): Use a scanned PDF (image-based PDF) to test the OCR pipeline. Docling’s OCR capability should extract text from images. We provide a sample scanned page along with its ground-truth text. The test will:
  - Run the conversion on the scanned PDF and capture the extracted text from the JSON output (likely under a text layer for the page).
  - Compare the extracted text with expected text (exact match or high similarity if minor OCR errors are tolerable).
  - Assert that the JSON indicates OCR was applied (e.g. a flag or presence of OCR-specific fields).
  - **Visualization**: output an image highlighting recognized text regions (e.g. outline each word detected on the scanned page) as `sample2_ocr.png`. This ensures the OCR bounding boxes align with the content.

- **Table Extraction** (`tests/tables/test_extraction.py`): Use PDFs containing tables (for instance, an academic paper with a table or a financial report). We verify that tables are identified and structured correctly in the JSON:
  - Confirm that the number of tables detected matches the known count in the document.
  - For each extracted table, check the dimensions (rows x columns) against the expected structure. For example, if the sample PDF has a 3x4 table, the JSON should reflect 3 rows and 4 columns with the correct content grouping.
  - Validate that the content of specific cells in the JSON matches the PDF (e.g. headers, or a known data cell).
  - If the format includes table coordinates or bounding boxes, ensure they are present and plausible (e.g. non-zero size).
  - **Visualization**: draw table grids on the page image (`sample3_tables.png`), e.g. outline each table’s boundary and cell borders if available. This will be saved and later linked in the test report for manual inspection of table structure detection.

- **Figure Detection and Extraction** (`tests/figures/test_detection.py`): Use PDFs with figures or images (diagrams, charts) to test figure extraction:
  - Ensure the number of figures in the output JSON matches the document (e.g. if the PDF has 2 figures, the JSON has 2 figure entries).
  - Each figure entry in JSON should have a bounding box and, if applicable, an associated caption text. We will verify that the caption text in the JSON matches the figure’s caption in the PDF.
  - If the pipeline extracts figure images or paths, verify the image is saved or referenced (for example, a path to an extracted image file or an encoded image).
  - **Visualization**: create an image (`sample4_figures.png`) drawing bounding boxes around detected figure regions, and perhaps overlay the caption text below each box. This confirms that our figure detector found the correct regions on the page.

- **Other Content & Metadata** (`tests/layout/test_misc.py`): Test any additional structured content that Docling/PaperMage handle, such as **footnotes, headers, references, code blocks, or formulas**:
  - *Headers/Footers*: Use a sample PDF with page headers/footers. Verify the converter correctly tags or excludes them as needed (e.g. if the expectation is that body text excludes running headers).
  - *References/Sections*: If the output format includes sections like title, authors, references, etc., verify those fields. For example, check that the document title and authors are correctly extracted for a given paper PDF.
  - *Code Blocks/Formulas*: If the Docling pipeline identifies code listings or math formulas, use a PDF containing these (e.g. an academic paper with an equation and a code snippet). Verify that:
    - Code blocks are captured distinctly (maybe as a separate layer or with a label in JSON).
    - Formulas/equations either appear as images or LaTeX strings in the JSON (depending on how docling outputs them).
  - *Logical Structure*: If using Docling’s logical structure models (e.g. segmenting abstract, body, etc.), ensure those segments appear in JSON as expected.
  - **Note**: These tests ensure that **every feature listed in Docling’s capabilities** (layout, tables, figures, etc.) ([GitHub - docling-project/docling: Get your documents ready for gen AI](https://github.com/docling-project/docling#:~:text=,Markdown%2C%20HTML%2C%20and%20lossless%20JSON)) is covered by at least one test.

Each feature test will not only assert the correctness of the JSON data but also validate against a **pre-recorded expected JSON** (stored in `tests/data/expected/`). This provides a snapshot test for the feature in a controlled scenario.

### 2. API Route Tests (`tests/api/test_routes.py`)

We will test the FastAPI endpoints using Starlette’s TestClient to simulate HTTP requests without running a live server. Key tests for the API layer:

- **Conversion Endpoint Success**: Simulate a POST to the document conversion endpoint (e.g. `POST /api/convert`) with a sample PDF file upload. Assert that:
  - The response HTTP status is 200 OK.
  - The response body JSON matches the expected output for that PDF (we load the corresponding golden JSON and compare). This effectively tests the full pipeline (FastAPI routing -> converter -> docling -> output).
  - The response headers (e.g. content-type `application/json`) are correct.
  - No unexpected fields or missing fields in the JSON (schema validation can be applied here as well).

- **Conversion Endpoint Error Handling**: Test various error conditions:
  - Uploading an invalid file type or corrupted PDF: e.g. `POST /api/convert` with a text file or a deliberately broken PDF. The service should respond with a 4xx status (likely 400 Bad Request) and a JSON error message. The test will verify the status code and that the JSON contains an `"error"` or `"detail"` field describing the issue.
  - Missing file: Call the endpoint without a file (if it’s required). Expect a 422 Unprocessable Entity or similar, and verify error response.
  - (If applicable) Unauthorized access or other security-related response codes, though if the API is open for these tests, this may not apply.

- **Healthcheck Endpoint**: If the backend provides a health or status endpoint (e.g. `GET /api/health`), ensure it returns the expected output (could be a simple JSON like `{"status": "ok"}` with 200 status). This ensures our test environment and server are running properly.

- **Multiple Requests**: Although largely an integration concern, we can optionally simulate multiple conversion calls (to ensure no state carry-over between requests). For example, call the conversion twice with the same file and ensure both responses are correct and independent.

These API tests ensure that the FastAPI layer correctly ties into the conversion logic and handles input/output as expected.

### 3. Converter Module and JSON Schema Tests

The **converter module** (`docling_papermage` in our code) is responsible for taking Docling’s output and producing a JSON matching PaperMage’s format. We will create tests specifically for this logic:

- **Unit Tests for Converter Functions** (`tests/converter/test_converter_module.py`): If the converter has sub-components (e.g. functions to process tables, figures, text blocks), we will directly test those with controlled inputs:
  - Simulate a minimal Docling document object (or parts of it) to feed into the converter. For instance, create a fake Docling table object with known cells, run the converter’s table serialization, and assert the JSON snippet matches expected structure.
  - Similarly, test converter handling of images: feed a dummy Docling image object and ensure the JSON output has the correct base64 or path reference and metadata.
  - Test merging of outputs: if the converter combines text, tables, figures into one JSON, ensure the final JSON has all sections correctly populated.

- **End-to-End JSON Conversion Test** (`tests/converter/test_full_conversion.py`): Using a real PDF input, run the Docling parser through the converter *without* the API layer. For example, call the converter function directly with a PDF path or a loaded Docling document. Then:
  - Load the corresponding expected JSON file from `tests/data/expected/`.
  - Compare the entire JSON structures for equality (or near-equality, considering minor variations like ID fields or timestamps which we can normalize or ignore in comparison).
  - This acts as a snapshot test for the whole conversion pipeline at the converter level.

- **JSON Schema Validation** (`tests/converter/test_schema_validation.py`): We will maintain a JSON Schema (or a pydantic model) that defines the expected PaperMage output format. This schema captures required fields (like `pages`, `figures`, `tables` arrays, etc.), data types, and nested structure. In this test:
  - Load each sample output JSON (either by running a conversion or using the golden files).
  - Validate it against the schema using a library like `jsonschema`. The test will fail if any required field is missing or any type mismatches.
  - We will include negative tests by intentionally altering a correct JSON to violate the schema (for instance, remove a required field) and confirming that the validator catches the error – this ensures our schema is effective.

By validating against a schema, we ensure consistency with the PaperMage output format and catch any drift that might occur due to the refactor.

### 4. Error Handling & Edge Case Tests (`tests/converter/test_edge_cases.py`)

To guarantee robustness, we design tests for problematic inputs and edge scenarios:

- **Corrupted PDF File**: Include a file in `tests/data/` that is not a valid PDF (e.g. a zero-byte file or a PDF with a broken header). When the converter attempts to process this, it should raise an exception or return an error. The test will assert that:
  - An appropriate Python exception is raised during conversion (e.g. `PdfReadError` from PyMuPDF or similar), which our converter module should catch.
  - The converter returns a defined error structure (if the design is to return JSON with error info) or that the API returns a 400 error with message (if tested via API).
  - No partial output JSON is produced on failure.

- **Missing Content**: Test PDFs that lack certain expected content:
  - **No Text PDF**: a PDF that contains only images (no extractable text). Our pipeline might rely on OCR in this case. We verify that the output JSON has either an empty text content or only images, but does not crash. If OCR is available, verify it kicks in.
  - **No Images/Graphics**: a PDF that is pure text (to ensure figure detection doesn’t produce false positives or errors).
  - **Empty PDF**: a PDF with zero pages (or only a cover page). The output should be basically empty or minimal JSON. Ensure the converter handles this gracefully (perhaps an empty pages list).
  - **Extreme Cases**: very large PDF, or a PDF with unusual fonts/encodings. We might not include a huge file in tests, but we can simulate aspects (like a page with thousands of words) by duplicating content to see if performance or memory issues arise in tests (if feasible with timeouts).

- **Malformed Metadata**: If our pipeline reads PDF metadata (author, title), test with a PDF that has corrupted or non-ASCII metadata. Ensure no encoding errors occur and that our JSON either omits invalid metadata or sanitizes it.

- **Docling Internal Failures**: Induce a failure in the Docling library (if possible, via monkeypatch or providing bad input). For example, if Docling’s parser throws an error for a certain content type, verify our wrapper catches it. This can be done by patching a Docling function to throw an exception and ensuring our converter handles it.

Each of these tests targets a different failure mode, asserting that the system either produces a clear error message or an empty result rather than crashing. By covering these, we ensure the backend is resilient and will maintain 100% coverage even over exception paths.

## Use of Real PDF Examples and Snapshots

A cornerstone of this strategy is **using real-world PDFs for tests**. Synthetic data or mocks are not sufficient for end-to-end validation of a PDF processing pipeline. We will collect a variety of sample PDFs in `tests/data/` to cover use cases:

- `tests/data/sample1_simple.pdf` – A simple text-only PDF (for baseline text extraction tests).
- `tests/data/sample2_multicolumn.pdf` – A multi-column paper to test layout and reading order.
- `tests/data/sample3_scanned.pdf` – A scanned document image to test OCR.
- `tests/data/sample4_tables.pdf` – A document with one or more tables.
- `tests/data/sample5_figures.pdf` – A document with figures and captions.
- `tests/data/sample6_mixed.pdf` – (Optional) a complex document with tables, figures, and text to test the pipeline holistically.
- `tests/data/corrupt.pdf` – An invalid PDF to test error handling.

For each sample PDF, we will have a corresponding **expected output JSON** in `tests/data/expected/` (or similar path). These JSON files serve as the “golden” reference outputs (snapshots). They can be obtained either from a known correct run of the previous PaperMage pipeline or generated once from the new pipeline and verified manually for correctness. They represent the *expected state of the system’s output*.

**Snapshot Comparison**: When tests run, after converting a PDF to JSON, we load the expected JSON and compare:
- We use deep equality for structured data, with possible normalization for non-deterministic fields (e.g. if timestamps or run IDs are included in output, our comparison will ignore or normalize those).
- If any difference is found, the test fails and highlights a diff (we can integrate a library to show JSON diffs for clarity).

This approach ensures that any change in the output (intentional or accidental) is caught. Intentional changes (e.g. improving table structure output) will cause tests to fail until we update the expected JSON files to the new correct output, which is a deliberate step by the developer (preventing silent regressions).

**Updating Snapshots**: We will make it straightforward to update the golden references when needed:
- If using a plugin like `pytest-regressions` or `pytest-approvaltests`, developers can run tests with a flag (e.g. `--force-regen` or an update command) which will rewrite the expected JSON files with the current output. We will document this process (see **Running Tests & Reports** below).
- If not using a plugin, we can provide a utility script (e.g. `tests/update_golden.py`) that runs the conversion on all sample PDFs and dumps new JSON files, which developers can use to replace the old ones after verifying changes.

All expected JSON files will be version-controlled. When outputs change legitimately, those diffs in JSON can be reviewed in code reviews to confirm the changes are as expected (e.g. a new field added, or improved OCR text).

## Visualization of Features in Tests

To enhance understanding and debugging, the test suite will produce **visual artifacts** for each tested document/feature and include them in the test results:

- All visualization images will be saved under `tests/visuals/`, following the naming convention `<docid>_<feature>.png`. For example, `sample3_tables.png` might show the table extraction result for sample3.
- We use Python libraries like Matplotlib or PIL to draw on images. Typically, we will render each PDF page (using a PDF rendering library or converting PDF to image) and then draw colored rectangles or labels:
  - **Text layout**: draw bounding boxes around words or lines, perhaps with line numbers to indicate reading order.
  - **Tables**: overlay a grid on detected tables, and label table boundaries.
  - **Figures**: outline figure regions with a box, and maybe number them (Fig1, Fig2, etc.) to cross-reference with captions.
  - **OCR**: highlight regions of detected text in the scanned image.
- The generation of these images will happen during the test execution. We ensure that each test knows the file path of its visualization so it can output or attach it.

Importantly, we will integrate these visuals into the **pytest HTML report** (described next) for easy viewing:
each test, upon success or failure, can attach the relevant image file as extra output. This way, when a developer opens the test report, they can click to see how the content was parsed (useful for diagnosing why a test might have failed).

These visualizations are **not** assertions themselves (tests don’t pass/fail based on images), but they are invaluable for manually verifying that the system “sees” the document correctly. They also serve as documentation of what the system extracted.

## Pytest Execution and HTML Reports

All tests will be written using **pytest**. Pytest’s fixtures and parametrization will be used to avoid code duplication (for example, a fixture might load all sample PDFs or provide a function to run a conversion easily).

We will use the **pytest-html** plugin to generate an **HTML test report** that includes our visual outputs and a summary of results. Key points:

- Running the test suite with `pytest` will execute all tests. To generate the HTML report, use:  
  ```bash
  pytest --html=reports/test_report.html --self-contained-html --capture=tee-sys
  ```  
  This will create a file `test_report.html` in the `reports/` directory (or a chosen location). The `--self-contained-html` flag ensures the report is a standalone file (with embedded CSS/JS) for easy sharing. The `--capture=tee-sys` ensures that even print output is captured in the report (useful if our tests print any debugging info or diffs).

- **Attaching Visuals**: We will configure our tests to attach the images in `tests/visuals/` to the report. Using `pytest-html` extras, after generating an image we can do something like:  
  ```python
  import pytest
  from pytest_html import extras
  
  def test_layout_extraction(record_property):
      # ... run test, save visualization to path_img ...
      record_property("extra", pytest_html.extras.image(str(path_img), mime_type="image/png"))
  ```  
  This will embed a thumbnail and link for the image in the report for that test case. Each test that produces a visualization will attach it similarly. The result is that for each test (e.g. table extraction on sample3), the HTML report will have a clickable link to `sample3_tables.png`. 

- **Report Contents**: The HTML report will show a summary (number of tests passed/failed) and for each test, its name, status, captured output, and our attached images. This provides a one-stop view to inspect all features’ outputs post-test. For example, a test failing a JSON comparison will show a diff in captured stdout (if we print the diff) and the image of that page to help pinpoint the difference.

- **Continuous Integration**: We will integrate the test run (with coverage) in CI. The HTML report can be stored as an artifact in CI for download, and the console output will also indicate any failures. Achieving 100% coverage will be verified by running `pytest --cov=semantic_reader_backend` (with `pytest-cov` plugin) and ensuring coverage is at 100% for all modules.

## Directory Structure and File Layout

The tests will be organized in a structured directory layout within the repository. Here’s the proposed structure and naming conventions:

```
semantic-reader-backend/
├── semantic_reader_backend/      # (source code)
│   ├── converter/                # converter module wrapping docling (refactored)
│   └── ... 
├── tests/
│   ├── data/
│   │   ├── sample1_simple.pdf
│   │   ├── sample2_multicolumn.pdf
│   │   ├── sample3_scanned.pdf
│   │   ├── sample4_tables.pdf
│   │   ├── sample5_figures.pdf
│   │   ├── sample6_mixed.pdf
│   │   ├── corrupt.pdf
│   │   └── expected/
│   │       ├── sample1_simple.json
│   │       ├── sample2_multicolumn.json
│   │       ├── sample3_scanned.json
│   │       ├── sample4_tables.json
│   │       ├── sample5_figures.json
│   │       └── sample6_mixed.json
│   ├── visuals/
│   │   ├── sample1_layout.png
│   │   ├── sample2_layout.png
│   │   ├── sample2_ocr.png
│   │   ├── sample3_tables.png
│   │   ├── sample4_figures.png
│   │   └── ... (etc for each doc/feature visualization)
│   ├── layout/
│   │   ├── test_lines.py           # Tests for page layout, lines, reading order
│   │   └── test_misc.py            # Tests for headers/footers, logical structure, etc.
│   ├── ocr/
│   │   └── test_ocr_extraction.py  # Tests for OCR on scanned PDFs
│   ├── tables/
│   │   ├── test_extraction.py      # Tests for table detection and structure
│   │   └── test_content.py         # (Optional) deeper tests on table cell content
│   ├── figures/
│   │   └── test_detection.py       # Tests for figure and caption extraction
│   ├── converter/
│   │   ├── test_converter_module.py  # Unit tests for converter functions
│   │   ├── test_full_conversion.py   # Integration test for converter end-to-end
│   │   ├── test_schema_validation.py # JSON schema compliance tests
│   │   └── test_edge_cases.py       # Error handling and edge case tests
│   └── api/
│       └── test_routes.py          # FastAPI endpoint integration tests
└── ...
```

This structure groups tests by feature area for clarity. Each test file focuses on a specific aspect or component. The `tests/data/` directory contains all sample inputs and expected outputs, and `tests/visuals/` contains generated images. 

Having `expected` JSONs versioned allows quick visual diffing if outputs change. The separation into subdirectories (layout, ocr, tables, figures, etc.) makes it easy to run a subset (e.g. `pytest tests/tables/` to just run table tests during development of that feature).

Below is a summary table of the features and their corresponding test files:

| **Feature / Area**                | **Test File(s)**                      |
|-----------------------------------|---------------------------------------|
| Page Layout & Reading Order       | `tests/layout/test_lines.py` (also visuals) |
| OCR Text Extraction (Scanned PDFs)| `tests/ocr/test_ocr_extraction.py`    |
| Table Detection & Structure       | `tests/tables/test_extraction.py` (and `test_content.py`) |
| Figure Detection & Captions       | `tests/figures/test_detection.py`     |
| Other Logical Structure (headers, etc.) | `tests/layout/test_misc.py`    |
| Converter Module (Docling -> JSON)| `tests/converter/test_converter_module.py` |
| Full Conversion Pipeline (snapshot)| `tests/converter/test_full_conversion.py` |
| JSON Schema Compliance            | `tests/converter/test_schema_validation.py` |
| Error Handling & Edge Cases       | `tests/converter/test_edge_cases.py`  |
| FastAPI API Endpoints             | `tests/api/test_routes.py`            |
| Visual Regression Artifacts       | (Generated in `tests/visuals/*.png` by tests above) |

This table of contents for tests ensures every feature and module of the backend is accounted for in our testing plan.

## Running the Test Suite and Viewing Reports

To run the entire test suite, developers can use the following commands:

1. **Install Test Dependencies**: Ensure `pytest`, `pytest-html`, `pytest-cov`, `jsonschema`, and any other test utilities (e.g. PDF rendering libs for visualization) are installed (these would be in the dev requirements).
2. **Execute Tests**: From the project root, run:  
   ```bash
   pytest --cov=semantic_reader_backend --html=reports/test_report.html --self-contained-html
   ```  
   This will run all tests, measure coverage, and generate the HTML report. The console output will show a summary of passed/failed tests and coverage percentage. We expect **100% coverage** – if coverage is below 100%, the build should be considered failing (we can enforce this with `--cov-fail-under=100` flag).

3. **Open the HTML Report**: After tests complete, open `reports/test_report.html` in a web browser. Navigate through the report to see results for each test. For any failures, the report will show the error, stack trace, and any captured stdout (which could include JSON diff). For all tests (pass or fail), look for the **attached visualization images** – you can click on them to open and inspect the rendered page with overlays (e.g. to confirm table boundaries or text ordering).

4. **Review Coverage**: Optionally, use `coverage html` to generate a coverage report (if using coverage.py). This lets you open `htmlcov/index.html` to see line-by-line coverage. However, given our goal of 100%, simply ensuring the percentage is at 100 in the console may suffice. All code paths, including error branches, should be executed by some test.

## Updating Expected Outputs (Snapshot Updates)

When intentional changes to the output format or content are made (for example, upgrading Docling might improve OCR accuracy or change how tables are represented), some tests comparing to expected JSON will fail. To update the snapshots (golden files):

- First, run the specific failing tests to see the differences. For instance, `pytest tests/tables/test_extraction.py -vv` will show which parts of the table JSON differ.
- Verify that these differences are expected and acceptable (e.g. a new field `confidence` was added to the output, or an OCR text improved).
- **Update the golden JSON files**: There are two ways:
  1. Manually update the JSON files in `tests/data/expected/`. You can copy the printed output from the failing test (some tests may log the new JSON) or re-run the converter and save its output. Ensure formatting (indentation) remains consistent.
  2. Use a pytest utility. If we integrate `pytest-regressions`, you can re-run tests with `--force-regen` to automatically overwrite expected files with new output. Alternatively, we provide a script to regenerate all expected JSONs:
      ```bash
      python tests/update_golden.py
      ```
     This script would iterate over sample PDFs, run conversion, and save JSON to `tests/data/expected/`. After running it, review the git diff of the JSON files to make sure changes are as intended.

- After updating, run the tests again. All tests should pass with the new expected outputs. Commit the updated JSON files along with any code changes.

By following this procedure, we maintain alignment between the test expectations and the evolving code, while still using tests to catch unintentional deviations. Always review changes to expected outputs – they effectively represent the “contract” of what the backend provides.

---

By implementing this testing strategy, the `semantic-reader-backend` project will gain a robust safety net. Every document-processing feature (from layout parsing to figure extraction) is validated with real examples, the FastAPI interface is verified, and the integration of Docling is proven to match the legacy PaperMage output format. The high coverage and use of visual and snapshot tests will make future refactoring or upgrades (e.g. updating the Docling library) much easier – any regression will be immediately caught, and developers will have clear diagnostics (via images and JSON diffs) to understand and fix issues. This test suite will thus ensure the reliability and correctness of the backend as it continues to evolve.  ([GitHub - docling-project/docling: Get your documents ready for gen AI](https://github.com/docling-project/docling#:~:text=,Markdown%2C%20HTML%2C%20and%20lossless%20JSON))