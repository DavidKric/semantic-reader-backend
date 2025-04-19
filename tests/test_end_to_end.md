# Test Guidelines: End-to-End Tests

## Purpose
End-to-end tests should simulate real user scenarios by interacting with your application's API or UI. **Do NOT** test Docling or PaperMage internals directly.

## Guidelines
- **Do NOT** directly import or test Docling or PaperMage classes/functions.
- **DO** use your application's API endpoints or UI to simulate user actions (e.g., file upload, report download).
- **Assert** on the outputs as a user would see them (e.g., API JSON, HTML reports).
- **Do NOT** compare or assert on Docling/PaperMage internal data structures.

## Recommended Test Flow
1. **Arrange:**
   - Prepare input data as a user would provide (e.g., PDF files).
2. **Act:**
   - Use the FastAPI test client to make HTTP requests to your API (e.g., upload a file, request a report).
3. **Assert:**
   - Check the HTTP response status, structure, and content as a user would see it.
   - Optionally, compare the output to a "golden" expected output, but only via your API.

## Example
```python
def test_document_processing_api(client):
    with open("sample.pdf", "rb") as f:
        response = client.post("/api/documents/process", files={"file": ("sample.pdf", f, "application/pdf")})
    assert response.status_code == 200
    data = response.json()
    assert "pages" in data
``` 