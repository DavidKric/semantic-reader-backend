#!/bin/bash
# setup_dev.sh - Set up a development environment using UV
set -e

# Constants
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check for UV
if ! command -v uv >/dev/null 2>&1; then
    echo -e "${YELLOW}UV not found. Installing...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo -e "${GREEN}UV installed successfully!${NC}"
else
    echo -e "${GREEN}UV already installed.${NC}"
    uv --version
fi

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
uv venv --python=3.11

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
uv pip install -e .

# Install development dependencies
echo -e "${YELLOW}Installing development dependencies...${NC}"
uv pip install -e ".[dev]"

# Generate lockfile
echo -e "${YELLOW}Generating lockfile...${NC}"
uv lock

echo -e "${GREEN}Development environment setup complete!${NC}"
echo -e "You can now activate the environment with: ${YELLOW}source .venv/bin/activate${NC}"
echo -e "Or run commands directly with: ${YELLOW}uv run <command>${NC}" 