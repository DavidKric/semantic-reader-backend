# Semantic Reader Backend Quick Start Guide

This guide will help you quickly set up and run the Semantic Reader Backend project.

## Prerequisites

- Python 3.11 or higher
- Bash shell (Linux/macOS) or Git Bash/WSL (Windows)

## Setup

### 1. Install UV

First, install the UV package manager globally:

```bash
curl -LsSf https://astral.sh/uv/install.sh | bash
```

Verify the installation:

```bash
uv --version
```

### 2. Set Up the Project

Navigate to the project root directory (where this QUICKSTART.md file is located) and run:

```bash
./docs/setup_uv.sh
```

This script will:
- Find the project root directory
- Install UV if not already installed
- Create a virtual environment
- Install all project dependencies

### 3. Activate the Virtual Environment

```bash
source .venv/bin/activate
```

## Project Structure

The project follows a standard Python src-layout:

```
semantic-reader-backend/
├── src/                         # Source code
│   └── papermage_docling/       # Main package
├── app.py                       # FastAPI app entry point
├── app/                         # FastAPI server components
├── scripts/                     # Utility scripts
│   ├── dev/                     # Development scripts
│   ├── ci/                      # CI/CD scripts
│   ├── utils/                   # Utility scripts
│   └── task-master/             # Task Management files
├── tests/                       # Test files
├── bin/                         # Convenience scripts
│   ├── setup                    # Quick setup script
│   └── test                     # Quick test runner
└── docs/                        # Documentation
```

## Running the Server

From the project root, run:

```bash
./run_server.sh
```

This will start the API server at http://localhost:8000

You can access:
- API Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Running Tests

Run all tests:

```bash
make test
```

Or run specific test types:

```bash
# Run unit tests
make test-unit

# Run end-to-end tests
make test-e2e

# Run tests with coverage report
make test-coverage
```

## Common Commands

```bash
# Check code quality
make quality-check

# Format code
make format

# Run linting
make lint

# Install dependencies
make dependencies

# Install development dependencies
make dev-dependencies
```

## Basic Usage Example

```python
from papermage_docling.parsers import DoclingPdfParser

# Create a parser instance
parser = DoclingPdfParser()

# Parse a PDF document
document = parser.parse("path/to/document.pdf", output_format="papermage")

# Print document metadata
print(document["document"]["metadata"])
```

## Troubleshooting

### Error: Not a Python Project

If you see an error like:
```
error: does not appear to be a Python project, as neither `pyproject.toml` nor `setup.py` are present
```

Make sure you are running the script from the project root directory (where pyproject.toml is located).

### Error: UV Not Found

If you see "UV not found" errors:

1. Try reinstalling UV:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | bash
   ```

2. Add it to your PATH:
   ```bash
   export PATH="$HOME/.cargo/bin:$PATH"
   ```

### Error: Missing Dependencies

If you see warnings about missing libraries for RTL or language detection:

```bash
# Install optional dependencies
uv pip install arabic-reshaper python-bidi langdetect fasttext
```

### Error: Virtual Environment Not Activating

If the virtual environment doesn't activate properly:

```bash
# Remove and recreate it
rm -rf .venv
./docs/setup_uv.sh
```

### Need More Information

For more detailed information:
- Read the comprehensive user guide in `docs/user_guide.md`
- Check the UV guides in `docs/uv_guide.md` and `docs/uv_quickstart.md`
- Run `make help` to see all available commands

## Support

If you continue experiencing issues, please open an issue on the GitHub repository. 