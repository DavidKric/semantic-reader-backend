#!/bin/bash
# quality_check.sh - Run code quality checks using UV
set -e

# Constants
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

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
    echo "  --all               Run all checks (default)"
    echo "  --lint              Run only linting"
    echo "  --format            Run only formatting"
    echo "  --typecheck         Run only type checking"
    echo "  --fix               Fix formatting issues"
    echo "  -v, --verbose       Run with verbose output"
    echo "  -h, --help          Show this help message"
    echo ""
}

# Default values
RUN_ALL=false
RUN_LINT=false
RUN_FORMAT=false
RUN_TYPECHECK=false
FIX_ISSUES=false
VERBOSE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            RUN_ALL=true
            shift
            ;;
        --lint)
            RUN_LINT=true
            shift
            ;;
        --format)
            RUN_FORMAT=true
            shift
            ;;
        --typecheck)
            RUN_TYPECHECK=true
            shift
            ;;
        --fix)
            FIX_ISSUES=true
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

# If no check type is specified, run all checks
if [[ "$RUN_ALL" == "false" && "$RUN_LINT" == "false" && "$RUN_FORMAT" == "false" && "$RUN_TYPECHECK" == "false" ]]; then
    RUN_ALL=true
fi

# Run linting
if [[ "$RUN_ALL" == "true" || "$RUN_LINT" == "true" ]]; then
    echo -e "${YELLOW}Running linting with Ruff...${NC}"
    if [[ "$FIX_ISSUES" == "true" ]]; then
        uv run ruff check --fix papermage_docling
    else
        uv run ruff check papermage_docling
    fi
    echo -e "${GREEN}Linting completed!${NC}"
fi

# Run formatting
if [[ "$RUN_ALL" == "true" || "$RUN_FORMAT" == "true" ]]; then
    echo -e "${YELLOW}Running formatting check...${NC}"
    if [[ "$FIX_ISSUES" == "true" ]]; then
        uv run ruff format papermage_docling
        echo -e "${GREEN}Files formatted!${NC}"
    else
        uv run ruff format --check papermage_docling
        echo -e "${GREEN}Format check completed!${NC}"
    fi
fi

# Run type checking
if [[ "$RUN_ALL" == "true" || "$RUN_TYPECHECK" == "true" ]]; then
    echo -e "${YELLOW}Running type checking with mypy...${NC}"
    uv run mypy papermage_docling
    echo -e "${GREEN}Type checking completed!${NC}"
fi

echo -e "${GREEN}All quality checks completed successfully!${NC}" 