#!/bin/bash
# Run tests for the Docling refactoring

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"

cd "$PROJECT_ROOT"

echo "===== Testing Docling Installation ====="
python scripts/tests/test_docling_installation.py

echo -e "\n===== Testing Converter ====="
python scripts/tests/test_converter.py

echo -e "\n===== Testing API ====="
python scripts/tests/test_api.py

echo -e "\n===== All tests completed successfully! =====" 