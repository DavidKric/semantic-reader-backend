#!/bin/bash

# migrate_to_uv.sh - Script to automate migration from pip to UV for Semantic Reader Backend
# This script performs the following actions:
# 1. Checks if UV is installed and installs it if necessary
# 2. Backs up existing requirements and virtual environment
# 3. Creates a new virtual environment with UV
# 4. Installs all dependencies using UV
# 5. Generates a lockfile for reproducible builds

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting migration from pip to UV...${NC}"

# Step 1: Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}UV not found. Installing...${NC}"
    curl -sSf https://astral.sh/uv/install.sh | bash
    
    # Verify installation
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}Failed to install UV. Please install manually:${NC}"
        echo "curl -sSf https://astral.sh/uv/install.sh | bash"
        exit 1
    fi
    echo -e "${GREEN}UV installed successfully.${NC}"
else
    echo -e "${GREEN}UV is already installed.${NC}"
fi

# Step 2: Create backup directory with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="./backup_pip_${TIMESTAMP}"
mkdir -p "$BACKUP_DIR"
echo -e "${GREEN}Created backup directory: ${BACKUP_DIR}${NC}"

# Step 3: Backup existing requirements files
files_backed_up=0

if [ -f "requirements.txt" ]; then
    cp requirements.txt "${BACKUP_DIR}/requirements.txt"
    echo -e "${GREEN}Backed up requirements.txt${NC}"
    ((files_backed_up++))
fi

if [ -f "requirements-dev.txt" ]; then
    cp requirements-dev.txt "${BACKUP_DIR}/requirements-dev.txt"
    echo -e "${GREEN}Backed up requirements-dev.txt${NC}"
    ((files_backed_up++))
fi

if [ -f "pyproject.toml" ]; then
    cp pyproject.toml "${BACKUP_DIR}/pyproject.toml"
    echo -e "${GREEN}Backed up pyproject.toml${NC}"
    ((files_backed_up++))
fi

if [ "$files_backed_up" -eq 0 ]; then
    echo -e "${YELLOW}Warning: No requirements files found to back up.${NC}"
fi

# Step 4: Backup existing virtual environment if it exists
if [ -d ".venv" ]; then
    echo -e "${YELLOW}Existing virtual environment found. Renaming to .venv_old${NC}"
    mv .venv .venv_old
    echo -e "${GREEN}Existing virtual environment backed up as .venv_old${NC}"
fi

# Step 5: Create new virtual environment with UV
echo -e "${GREEN}Creating new virtual environment with UV...${NC}"
uv venv
echo -e "${GREEN}Virtual environment created.${NC}"

# Step 6: Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"

# Determine which file to use for installation
if [ -f "pyproject.toml" ]; then
    echo -e "${GREEN}Found pyproject.toml, installing in editable mode...${NC}"
    uv pip install -e ".[dev,test]"
elif [ -f "requirements.txt" ]; then
    echo -e "${GREEN}Found requirements.txt, installing...${NC}"
    uv pip install -r requirements.txt
    
    if [ -f "requirements-dev.txt" ]; then
        echo -e "${GREEN}Found requirements-dev.txt, installing...${NC}"
        uv pip install -r requirements-dev.txt
    fi
else
    echo -e "${YELLOW}Warning: No requirements files or pyproject.toml found. No dependencies installed.${NC}"
fi

# Step 7: Generate lockfile for reproducible builds
echo -e "${GREEN}Generating lockfile for reproducible builds...${NC}"
uv lock

# Step 8: Verify installation
echo -e "${GREEN}Verifying installation...${NC}"
PACKAGE_COUNT=$(uv pip list | wc -l)
echo -e "${GREEN}Successfully installed $(($PACKAGE_COUNT-2)) packages.${NC}"

echo -e "${GREEN}Migration from pip to UV completed successfully!${NC}"
echo -e "${GREEN}Your old virtual environment has been preserved as .venv_old${NC}"
echo -e "${GREEN}To activate the new environment:${NC}"
echo -e "${YELLOW}source .venv/bin/activate${NC}"
echo -e "${GREEN}For more information on using UV, visit: https://github.com/astral-sh/uv${NC}" 