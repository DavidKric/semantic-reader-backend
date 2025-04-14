# UV Comprehensive Guide

This guide provides detailed information about using UV (the fast Python package installer) with Semantic Reader Backend.

## Table of Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [Virtual Environments](#virtual-environments)
- [Package Management](#package-management)
- [Lockfiles](#lockfiles)
- [Migration from pip](#migration-from-pip)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Introduction

UV is a modern Python package installer and resolver written in Rust. It's designed to be a fast, reliable alternative to pip, pip-compile, and virtualenv. Some benefits of UV include:

- **Speed**: UV can install packages 10-100x faster than pip
- **Reliability**: Consistent dependency resolution across environments
- **Compatibility**: Works with existing Python tools and workflows
- **Unified toolchain**: Replaces multiple tools with a single command

## Installation

### Installing UV

```bash
# Install UV using the official installer script
curl -sSf https://astral.sh/uv/install.sh | bash

# Or with pipx
pipx install uv

# Or with Homebrew on macOS
brew install uv
```

### Verifying Installation

```bash
uv --version
```

## Virtual Environments

### Creating a Virtual Environment

```bash
# Create a new virtual environment in the .venv directory
uv venv

# Create a virtual environment with a specific Python version
uv venv --python=python3.9
```

### Activating the Environment

```bash
# On macOS/Linux
source .venv/bin/activate

# On Windows (Command Prompt)
.venv\Scripts\activate.bat

# On Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### Deactivating the Environment

```bash
deactivate
```

## Package Management

### Installing Project Dependencies

```bash
# Install all dependencies, including development packages
uv pip install -e ".[dev,test]"

# Install only the base dependencies
uv pip install -e .

# Install from requirements.txt
uv pip install -r requirements.txt
```

### Managing Individual Packages

```bash
# Install a specific package
uv pip install package_name

# Install a specific version
uv pip install package_name==1.2.3

# Upgrade a package
uv pip install --upgrade package_name

# Uninstall a package
uv pip uninstall package_name

# List installed packages
uv pip list

# Generate requirements from the current environment
uv pip freeze > requirements.txt
```

## Lockfiles

UV supports lockfiles which guarantee reproducible environments by exactly specifying package versions and hashes.

### Creating a Lockfile

```bash
# Create a lockfile from pyproject.toml
uv lock

# Create a lockfile from requirements.txt
uv lock -r requirements.txt -o requirements.lock
```

### Installing from a Lockfile

```bash
# Install dependencies from a lockfile
uv pip install --lockfile
```

### Updating a Lockfile

```bash
# Update the lockfile
uv lock --update
```

## Migration from pip

This project includes a migration script to help you transition from pip to UV.

### Using the Migration Script

```bash
# Run the migration script
bash scripts/migrate_to_uv.sh
```

The script performs the following actions:
1. Checks if UV is installed
2. Backs up existing requirements files
3. Creates a new virtual environment using UV
4. Installs dependencies from either requirements files or pyproject.toml
5. Generates a lockfile for reproducible builds

### Manual Migration

If you prefer to migrate manually, follow these steps:

1. Install UV: `curl -sSf https://astral.sh/uv/install.sh | bash`
2. Create a new environment: `uv venv`
3. Activate the environment: `source .venv/bin/activate`
4. Install dependencies: `uv pip install -e ".[dev,test]"`
5. Generate a lockfile: `uv lock`

## Troubleshooting

### Common Issues

1. **UV not found in PATH**
   - Ensure UV is installed correctly
   - Add UV to your PATH: `export PATH="$HOME/.cargo/bin:$PATH"`

2. **Permission errors during installation**
   - Try using sudo for the installation: `sudo curl -sSf https://astral.sh/uv/install.sh | sudo bash`
   
3. **Dependency resolution conflicts**
   - Check for incompatible version constraints in pyproject.toml
   - Try running with verbose output: `uv pip install -e . -v`

4. **Virtual environment activation issues**
   - Ensure the activation script is executable: `chmod +x .venv/bin/activate`
   - Try creating a new environment: `uv venv --force`

### Getting Help

If you encounter issues with UV:
- Check the [official UV documentation](https://github.com/astral-sh/uv)
- Open an issue in the project repository
- Consult the UV community on GitHub

## Best Practices

1. **Always use a virtual environment**
   - Create a dedicated environment for each project
   - Keep your global Python installation clean

2. **Use lockfiles for reproducibility**
   - Generate and commit lockfiles to ensure consistent builds
   - Update lockfiles intentionally with `uv lock --update`

3. **Keep dependencies minimal**
   - Only add dependencies that are actually needed
   - Regularly review and prune unused dependencies

4. **Follow a consistent workflow**
   - Install: `uv pip install -e ".[dev,test]"`
   - Develop and test
   - Update pyproject.toml when adding dependencies
   - Lock: `uv lock`
   - Commit both code and lockfile changes

5. **Use UV's performance benefits**
   - Run commands with `--no-cache` for fresh installs when needed
   - Use parallel installations with `--parallel` 