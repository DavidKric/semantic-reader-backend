# Test Guidelines: ocr

## Purpose
This folder should contain tests for your application's OCR (Optical Character Recognition) extraction features, **not** for Docling internals.

## Guidelines
- **Do NOT** directly import or test Docling classes/functions.
- **DO** test your own service layer (e.g., `OcrExtractionService`) or API endpoints.
- **Mock** Docling outputs if needed, but only to simulate their integration with your service.
- **Assert** on your service's or API's return values and business logic, not on third-party library internals.

## Recommended Test Flow
1. **Arrange:**
   - Mock Docling dependencies if your service uses them.
   - Prepare input data as your service or API expects (e.g., file paths, document objects).
2. **Act:**
   - Call your service's OCR extraction method or make an API request.
3. **Assert:**
   - Check that the output matches your application's expected structure and business rules.
   - Do not assert on Docling internal data structures.

## Example (Service)
```python
from app.services.ocr_extraction_service import OcrExtractionService

def test_ocr_extraction_service(mocker):
    mocker.patch("app.services.ocr_extraction_service.DoclingPdfParser.parse", return_value={"text_blocks": [{"text": "Sample text"}]})
    service = OcrExtractionService()
    result = service.extract_text("sample.pdf")
    assert result == [{"text": "Sample text"}]
```

## Example (API)
```python
def test_api_ocr_extraction(client):
    with open("sample.pdf", "rb") as f:
        response = client.post("/api/ocr/extract", files={"file": ("sample.pdf", f, "application/pdf")})
    assert response.status_code == 200
    data = response.json()
    assert "text_blocks" in data
``` 