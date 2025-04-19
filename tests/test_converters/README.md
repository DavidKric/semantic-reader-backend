# Test Guidelines: test_converters

## Purpose
This folder should contain tests for your application's document conversion services, **not** for Docling or PaperMage internals.

## Guidelines
- **Do NOT** directly import or test Docling or PaperMage classes/functions.
- **DO** test your own service layer (e.g., `DocumentProcessingService`) as it is used in your application.
- **Mock** Docling/PaperMage outputs if needed, but only to simulate their integration with your service.
- **Assert** on your service's return values and business logic, not on third-party library internals.

## Recommended Test Flow
1. **Arrange:**
   - Mock Docling/PaperMage dependencies if your service uses them.
   - Prepare input data as your service expects (e.g., file paths, document objects).
2. **Act:**
   - Call your service's conversion method (e.g., `service.convert_document(...)`).
3. **Assert:**
   - Check that the output matches your application's expected structure and business rules.
   - Do not assert on Docling/PaperMage internal data structures.

## Example
```python
from app.services.document_processing_service import DocumentProcessingService

def test_service_conversion(mocker):
    mocker.patch("app.services.document_processing_service.DoclingToPaperMageConverter.convert_docling_document", return_value={"symbols": "abc"})
    service = DocumentProcessingService()
    result = service.process_docling_document("fake_path.pdf")
    assert "symbols" in result
``` 