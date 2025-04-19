# Test Data Directory Structure

This directory contains test data organized according to pytest best practices. The structure is designed to be predictable, maintainable, and scalable.

## Directory Structure

```
tests/data/
├── fixtures/              # Test fixtures (input files and expected outputs)
│   ├── samples/           # Sample input files organized by type
│   │   ├── simple/        # Simple document samples
│   │   ├── complex/       # Complex document samples
│   │   ├── tables/        # Documents with tables
│   │   ├── figures/       # Documents with figures
│   │   ├── multi_column/  # Multi-column document samples
│   │   ├── rtl/           # Right-to-left language document samples
│   │   ├── large/         # Large document samples
│   │   ├── corrupt/       # Corrupt files for testing error handling
│   │   └── invalid/       # Invalid files (non-PDF) for testing error handling
│   └── expected/          # Expected outputs for tests
├── temp/                  # Temporary files created during tests
└── cache/                 # Cache directories for the application
    ├── papermage/         # Cache for PaperMage
    └── papermage_docling/ # Cache for PaperMage-Docling
```

## Access in Tests

The test fixtures are accessed through fixtures defined in `conftest.py`. To use them in your tests:

```python
import pytest
from pathlib import Path

def test_something(sample_pdfs, expected_outputs, temp_dir):
    # Access sample PDFs
    simple_pdf = sample_pdfs["simple"]
    
    # Access expected outputs
    expected = expected_outputs["sample1_simple"]
    
    # Use temp directory for test outputs
    output_path = temp_dir / "test_output.json"
    
    # Test logic here...
```

## Managing Test Data

### Adding New Sample Files

1. Place new sample files in the appropriate subdirectory under `fixtures/samples/`
2. Update the relevant fixtures in `conftest.py` if needed

### Adding Expected Outputs

1. Place expected JSON outputs in `fixtures/expected/`
2. Use meaningful names that match the sample files they correspond to

### Temporary Test Files

- Use the `temp_dir` fixture for any files created during tests
- These files are automatically cleaned up after tests run

## Setup Script

If the directory structure is not already set up, you can run the setup script:

```bash
python tests/scripts/setup_test_data.py
```

This will create the directory structure and migrate existing files to their proper locations.

## Best Practices

1. **Isolation**: Keep test data separate from test code
2. **Organization**: Use subdirectories to organize different types of test data
3. **Fixtures**: Access test data through pytest fixtures
4. **Cleanup**: Always clean up temporary files after tests
5. **Parametrization**: Use pytest's parametrize to run tests with different data inputs
6. **Documentation**: Document test data structure and usage 