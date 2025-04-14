# UV Migration Guide

This guide will help you transition from using pip to UV (µv) for package management in the Semantic Reader Backend project.

## What is UV?

UV is a modern Python package manager and installer written in Rust that aims to be a faster, more reliable replacement for pip. It offers significant performance improvements while maintaining compatibility with existing Python tooling.

Key benefits include:
- **Speed**: 10-100x faster than pip for installations and dependency resolution
- **Reliability**: More deterministic dependency resolution
- **Compatibility**: Works with existing requirements files and pyproject.toml
- **Modern features**: Built-in environment management and lockfile support

## Migration Process

### Automated Migration

The easiest way to migrate is to use our provided migration script:

```bash
# Make the script executable
chmod +x scripts/migrate_to_uv.sh

# Run the migration script
./scripts/migrate_to_uv.sh
```

The script will:
1. Install UV if it's not already installed
2. Back up your existing requirements files and virtual environment
3. Create a new virtual environment using UV
4. Install dependencies using UV
5. Generate a lockfile for reproducible builds

### Manual Migration

If you prefer to migrate manually, follow these steps:

1. **Install UV**:
   ```bash
   curl -sSf https://astral.sh/uv/install.sh | bash
   ```

2. **Backup existing environment**:
   ```bash
   # Rename existing virtual environment
   mv .venv .venv_old
   ```

3. **Create a new virtual environment with UV**:
   ```bash
   uv venv
   source .venv/bin/activate
   ```

4. **Install dependencies**:
   ```bash
   # If using pyproject.toml
   uv pip install -e ".[dev,test]"
   
   # If using requirements.txt
   uv pip install -r requirements.txt
   # And optionally dev requirements
   uv pip install -r requirements-dev.txt
   ```

5. **Generate a lockfile for reproducibility**:
   ```bash
   uv lock
   ```

## Command Reference

Below is a comparison of pip commands with their UV equivalents:

### Basic Package Management

| Task | pip Command | UV Command |
|------|------------|------------|
| Install a package | `pip install <package>` | `uv pip install <package>` |
| Install from requirements | `pip install -r requirements.txt` | `uv pip install -r requirements.txt` |
| Install editable package | `pip install -e .` | `uv pip install -e .` |
| Uninstall a package | `pip uninstall <package>` | `uv pip uninstall <package>` |
| List installed packages | `pip list` | `uv pip list` |
| Show package info | `pip show <package>` | `uv pip show <package>` |

### Environment Management

| Task | Traditional Method | UV Command |
|------|-------------------|------------|
| Create virtual environment | `python -m venv .venv` | `uv venv` |
| Activate environment | `source .venv/bin/activate` | `source .venv/bin/activate` (same) |
| Create & install from requirements | `python -m venv .venv && pip install -r requirements.txt` | `uv venv -r requirements.txt` |

### Advanced Features

| Task | Traditional Method | UV Command |
|------|-------------------|------------|
| Generate lockfile | N/A (pip has no built-in lockfile) | `uv lock` |
| Install from lockfile | N/A | `uv pip sync` |
| Run with specific Python | `python3.10 -m pip install ...` | `uv pip --python=python3.10 install ...` |

## Frequently Asked Questions

### Will my existing requirements files work with UV?

Yes, UV is designed to work with existing requirements.txt and pyproject.toml files.

### Do I need to update my CI/CD pipelines?

Yes, but the changes are minimal. Simply replace pip install commands with uv pip install, and if you use venv creation, replace it with uv venv.

### What about editable installs?

Editable installs are fully supported with the -e flag, just as with pip.

### How do I revert back to pip?

If you need to revert to pip for any reason:

1. Rename or delete the UV-created environment:
   ```bash
   # Rename UV environment
   mv .venv .venv_uv
   # Restore pip environment if you have a backup
   mv .venv_old .venv
   ```

2. Or create a new environment with pip:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   # Install from requirements
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

## Additional Resources

- [UV GitHub Repository](https://github.com/astral-sh/uv)
- [UV Documentation](https://astral.sh/uv)
- [Comparison with other package managers](https://astral.sh/blog/uv) 