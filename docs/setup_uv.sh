#!/bin/bash

# setup_uv.sh - UV setup script for Semantic Reader Backend
# This script installs UV, creates a virtual environment, and installs project dependencies

set -e  # Exit on any error

echo "Setting up UV for Semantic Reader Backend..."

# Find the project root directory (where pyproject.toml is)
# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

# Navigate up until we find pyproject.toml or hit the filesystem root
while [[ "$PROJECT_ROOT" != "/" && ! -f "$PROJECT_ROOT/pyproject.toml" ]]; do
    PROJECT_ROOT="$(dirname "$PROJECT_ROOT")"
done

if [[ ! -f "$PROJECT_ROOT/pyproject.toml" ]]; then
    echo "Error: Could not find pyproject.toml in any parent directory. Are you sure you're in the Semantic Reader Backend project?"
    exit 1
fi

echo "Found project root at: $PROJECT_ROOT"
cd "$PROJECT_ROOT"
echo "Working directory: $(pwd)"

# Check if UV is already installed
if command -v uv &> /dev/null; then
    echo "UV is already installed."
else
    echo "Installing UV..."
    curl -sSf https://astral.sh/uv/install.sh | bash
    
    # Reload shell configuration to make UV available
    if [[ -f ~/.zshrc ]]; then
        source ~/.zshrc
    elif [[ -f ~/.bashrc ]]; then
        source ~/.bashrc
    fi
    
    # Verify installation
    if ! command -v uv &> /dev/null; then
        echo "UV installation failed. Please install manually:"
        echo "curl -sSf https://astral.sh/uv/install.sh | bash"
        exit 1
    fi
fi

echo "Creating virtual environment..."
uv venv

echo "Activating virtual environment..."
source .venv/bin/activate || { echo "Failed to activate virtual environment"; exit 1; }

echo "Installing project dependencies..."
uv pip install -e ".[dev,test]" || { echo "Failed to install dependencies"; exit 1; }

echo "Setup complete!"
echo ""
echo "To activate the virtual environment in the future, run:"
echo "source $PROJECT_ROOT/.venv/bin/activate"
echo ""
echo "For more information on using UV, see:"
echo "- $PROJECT_ROOT/docs/uv_quickstart.md for quick reference"
echo "- $PROJECT_ROOT/docs/uv_guide.md for comprehensive documentation"
echo "- https://github.com/astral-sh/uv for official documentation" 