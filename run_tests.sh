#!/bin/bash
# Test runner script for semantic-reader-backend

set -e

# Set text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Display header
function show_header() {
  echo -e "\n${BLUE}┌─────────────────────────────────────────────┐${NC}"
  echo -e "${BLUE}│     Semantic Reader Backend Test Runner     │${NC}"
  echo -e "${BLUE}└─────────────────────────────────────────────┘${NC}\n"
}

# Install dependencies if needed
function install_deps() {
  echo -e "${YELLOW}Installing test dependencies...${NC}"
  
  # Ensure the tests/reporting directory exists
  mkdir -p tests/reporting
  
  # Create requirements file if it doesn't exist
  if [ ! -f "tests/reporting/requirements-test.txt" ]; then
    echo -e "${YELLOW}Creating test requirements file...${NC}"
    cat > tests/reporting/requirements-test.txt << EOL
# Test dependencies for reporting module
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
EOL
  fi
  
  # Install dependencies
  uv pip install -r tests/reporting/requirements-test.txt
  
  echo -e "${GREEN}Dependencies installed successfully.${NC}"
}

# Run a simple test script
function run_simple_test() {
  script_path=$1
  
  echo -e "\n${BLUE}Running test: ${script_path}${NC}"
  echo -e "${BLUE}$(printf '%.0s─' {1..50})${NC}"
  
  python "$script_path"
  
  if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ Test passed!${NC}"
    return 0
  else
    echo -e "\n${RED}✗ Test failed!${NC}"
    return 1
  fi
}

# Show usage information
function show_usage() {
  echo -e "Usage: $0 [options] [test_file]"
  echo -e "\nOptions:"
  echo -e "  -a, --all           Run all tests"
  echo -e "  -i, --isolated      Run isolated tests (no app imports)"
  echo -e "  -p, --pytest        Run pytest tests"
  echo -e "  -h, --help          Show this help message"
  echo -e "\nExamples:"
  echo -e "  $0 --all            Run all tests"
  echo -e "  $0 --isolated       Run isolated tests"
  echo -e "  $0 isolated_test_report.py  Run a specific test file"
}

# Run all isolated tests
function run_isolated_tests() {
  echo -e "${YELLOW}Running all isolated tests...${NC}"
  
  failures=0
  run_simple_test "isolated_test_report.py" || ((failures++))
  run_simple_test "simple_test_service_mock.py" || ((failures++))
  
  if [ $failures -eq 0 ]; then
    echo -e "\n${GREEN}All isolated tests passed!${NC}"
    return 0
  else
    echo -e "\n${RED}$failures test(s) failed!${NC}"
    return 1
  fi
}

# Edit run_tests.sh to include full test suite
function run_all_tests() {
  echo -e "${YELLOW}Running all tests...${NC}"
  python -m pytest tests/
}

# Main logic
function main() {
  show_header
  install_deps
  
  # Process arguments
  if [ $# -eq 0 ]; then
    run_isolated_tests
    return $?
  fi
  
  case "$1" in
    -h|--help)
      show_usage
      return 0
      ;;
    -a|--all|-s|--simple)
      echo -e "${YELLOW}Running all tests...${NC}"
      run_isolated_tests
      return $?
      ;;
    -i|--isolated)
      run_isolated_tests
      return $?
      ;;
    -p|--pytest)
      echo -e "${YELLOW}Running pytest tests...${NC}"
      python -m pytest tests/reporting -xvs
      return $?
      ;;
    *)
      if [ -f "$1" ]; then
        run_simple_test "$1"
        return $?
      else
        echo -e "${RED}Error: File '$1' not found!${NC}"
        show_usage
        return 1
      fi
      ;;
  esac
}

# Run the script
main "$@" 