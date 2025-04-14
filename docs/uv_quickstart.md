# UV Quickstart Guide

This guide provides a quick introduction to using UV with Semantic Reader Backend.

## What is UV?

UV is a fast Python package installer and resolver, written in Rust. It's designed to be a drop-in replacement for pip and virtualenv, with significantly improved performance.

## Basic Usage

### Creating a Virtual Environment

```bash
# Create a new virtual environment in the .venv directory
uv venv
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

### Installing Dependencies

```bash
# Install all project dependencies (including dev and test)
uv pip install -e ".[dev,test]"

# Or just the base dependencies
uv pip install -e .
```

### Managing Packages

```bash
# Install a package
uv pip install package_name

# Uninstall a package
uv pip uninstall package_name

# List installed packages
uv pip list

# Generate requirements from the current environment
uv pip freeze > requirements.txt
```

### Creating/Updating Lockfiles

```bash
# Generate or update the lockfile (requirements.lock)
uv lock
```

## Migrating from pip

If you're migrating from pip to UV, use the provided migration script:

```bash
# Run the migration script
bash scripts/migrate_to_uv.sh
```

For more detailed information about UV, see the [UV Guide](uv_guide.md) or visit the [official UV documentation](https://github.com/astral-sh/uv). 