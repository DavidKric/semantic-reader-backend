#!/bin/bash
# run_tests.sh - Run tests using UV
set -e

# Constants
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Activate virtual environment if it exists but is not activated
if [ -d ".venv" ] && [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv/bin/activate
fi

# Check for UV
if ! command -v uv >/dev/null 2>&1; then
    echo -e "${RED}UV not found. Please install it first:${NC}"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Function to show help message
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --all               Run all tests"
    echo "  --e2e               Run only end-to-end tests"
    echo "  --unit              Run only unit tests"
    echo "  --coverage          Generate coverage report"
    echo "  --html              Generate HTML report"
    echo "  -v, --verbose       Run with verbose output"
    echo "  -h, --help          Show this help message"
    echo ""
}

# Default values
RUN_ALL=false
RUN_E2E=false
RUN_UNIT=false
COVERAGE=false
HTML_REPORT=false
VERBOSE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            RUN_ALL=true
            shift
            ;;
        --e2e)
            RUN_E2E=true
            shift
            ;;
        --unit)
            RUN_UNIT=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --html)
            HTML_REPORT=true
            shift
            ;;
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# If no test type is specified, run all tests
if [[ "$RUN_ALL" == "false" && "$RUN_E2E" == "false" && "$RUN_UNIT" == "false" ]]; then
    RUN_ALL=true
fi

# Build command - use python directly as uv run can cause dependency issues
CMD="python -m pytest"

# Add verbosity if requested
if [[ -n "$VERBOSE" ]]; then
    CMD="$CMD $VERBOSE"
fi

# Add coverage if requested
if [[ "$COVERAGE" == "true" ]]; then
    CMD="$CMD --cov=papermage_docling --cov-report=term"
    
    if [[ "$HTML_REPORT" == "true" ]]; then
        CMD="$CMD --cov-report=html"
    fi
fi

# Add HTML report if requested
if [[ "$HTML_REPORT" == "true" && "$COVERAGE" == "false" ]]; then
    CMD="$CMD --html=report.html"
fi

# Run appropriate tests
if [[ "$RUN_ALL" == "true" ]]; then
    echo -e "${YELLOW}Running all tests...${NC}"
    $CMD
elif [[ "$RUN_E2E" == "true" ]]; then
    echo -e "${YELLOW}Running end-to-end tests...${NC}"
    $CMD papermage_docling/tests/test_end_to_end.py
elif [[ "$RUN_UNIT" == "true" ]]; then
    echo -e "${YELLOW}Running unit tests...${NC}"
    $CMD $(find papermage_docling/tests -name "test_*.py" -not -name "test_end_to_end.py")
fi

echo -e "${GREEN}Tests completed!${NC}" 