# Reporting Module Tests

This directory contains tests for the HTML report generation and visualization functionality of the Semantic Reader Backend.

## Test Structure

- `test_html_generator.py`: Tests for the HTML report generator
- `test_visualizations.py`: Tests for document visualization functions
- `test_service.py`: Tests for the report service
- `requirements-test.txt`: Specific dependencies for these tests

## Running Tests

There are several ways to run the tests:

### 1. Using the test runner script

We provide a convenient test runner script that handles dependencies and can run all tests:

```bash
# Run all tests
./run_tests.sh 

# Run all simple tests (without pytest)
./run_tests.sh --simple

# Run a specific test file
./run_tests.sh simple_test_report.py

# Run pytest tests
./run_tests.sh --pytest
```

### 2. Running individual test files directly

You can run the simple test scripts directly:

```bash
python simple_test_report.py
python simple_test_visualizations.py
python simple_test_service_mock.py
```

### 3. Using pytest

For more detailed test reports and coverage information:

```bash
# Install test requirements first
uv pip install -r tests/reporting/requirements-test.txt

# Run tests with pytest
python -m pytest tests/reporting -v

# Run with coverage report
python -m pytest tests/reporting -v --cov=app.reporting
```

## Dependency Issues

If you encounter dependency issues, make sure you're using the specific package versions listed in `requirements-test.txt`. The current versions that work well together are:

```
pytest==7.3.1
pytest-cov==4.1.0
matplotlib==3.7.1
numpy==1.24.3
pydantic==1.10.7
fastapi==0.95.1
starlette==0.26.1
httpx==0.24.1
beautifulsoup4==4.12.2
coverage==7.8.0
```

The specific combination of `pydantic==1.10.7`, `fastapi==0.95.1`, and `starlette==0.26.1` is important to avoid import errors.

## Adding New Tests

When adding new tests:

1. For simple tests, create a new Python file named `simple_test_*.py` in the project root
2. For pytest tests, add them to the appropriate subdirectory under `tests/`
3. Update the `run_tests.sh` script if needed to include your new test

## Troubleshooting

If you encounter issues:

- Check that you have the correct dependency versions installed
- Try using `uv pip install -r tests/reporting/requirements-test.txt` to install the correct dependencies
- Look for import errors related to pydantic, which is a common source of problems 