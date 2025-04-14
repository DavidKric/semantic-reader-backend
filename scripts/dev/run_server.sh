#!/bin/bash

# run_server.sh - Script to run the Semantic Reader Backend server
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Semantic Reader Backend server...${NC}"

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}Error: UV not found. Please install it first:${NC}"
    echo "curl -LsSf https://astral.sh/uv/install.sh | bash"
    exit 1
fi

# Set environment variables explicitly without any comments or whitespace
export APP_NAME="Semantic Reader Backend"
export APP_VERSION="0.1.0"
export API_VERSION="v1"
export HOST="0.0.0.0"
export PORT=8000
export WORKERS_COUNT=1
export DEBUG_MODE=false
export LOG_LEVEL="INFO"
export LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
export ALLOWED_ORIGINS_STR="*"
export RATE_LIMIT_ENABLED=false
export RATE_LIMIT_REQUESTS=100
export RATE_LIMIT_PERIOD=60
export ENABLE_UI=true
export MODEL="claude-3-7-sonnet-20250219"
export PERPLEXITY_MODEL="sonar-pro"
export MAX_TOKENS=64000
export TEMPERATURE=0.2
export DEFAULT_SUBTASKS=5
export DEFAULT_PRIORITY="medium"
export PROJECT_NAME="papermage-docling"

# Document processing settings
export OCR_ENABLED=false
export OCR_LANGUAGE="eng"
export DETECT_RTL=true
export ALLOWED_EXTENSIONS="pdf,docx,txt"
export MAX_FILE_SIZE_MB=50

# Print instructions
echo -e "${YELLOW}Starting server...${NC}"
echo -e "Once the server is running, you can access:"
echo -e "- API: ${GREEN}http://localhost:8000${NC}"
echo -e "- API Documentation: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "- ReDoc: ${GREEN}http://localhost:8000/redoc${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Use UV to run the application using FastAPI best practices
echo -e "${YELLOW}Running with UV to ensure proper dependency management...${NC}"

# UV FastAPI running options:
# 1. Run app.py directly with uvicorn through UV
# 2. Run app module with UV run

uv run uvicorn app:app --reload --host $HOST --port $PORT 