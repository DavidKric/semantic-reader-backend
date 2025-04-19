# Test Guidelines: figures

## Purpose
This folder should contain tests for your application's figure detection and extraction features, **not** for Docling internals.

## Guidelines
- **Do NOT** directly import or test Docling classes/functions.
- **DO** test your own service layer (e.g., `FigureDetectionService`) or API endpoints.
- **Mock** Docling outputs if needed, but only to simulate their integration with your service.
- **Assert** on your service's or API's return values and business logic, not on third-party library internals.

## Recommended Test Flow
1. **Arrange:**
   - Mock Docling dependencies if your service uses them.
   - Prepare input data as your service or API expects (e.g., file paths, document objects).
2. **Act:**
   - Call your service's figure detection method or make an API request.
3. **Assert:**
   - Check that the output matches your application's expected structure and business rules.
   - Do not assert on Docling internal data structures.

## Example (Service)
```python
from app.services.figure_detection_service import FigureDetectionService

def test_figure_detection_service(mocker):
    mocker.patch("app.services.figure_detection_service.DoclingPdfParser.parse", return_value={"figures": [{"id": 1}]})
    service = FigureDetectionService()
    result = service.extract_figures("sample.pdf")
    assert result == [{"id": 1}]
```

## Example (API)
```python
def test_api_figure_detection(client):
    with open("sample.pdf", "rb") as f:
        response = client.post("/api/figures/extract", files={"file": ("sample.pdf", f, "application/pdf")})
    assert response.status_code == 200
    data = response.json()
    assert "figures" in data
``` 