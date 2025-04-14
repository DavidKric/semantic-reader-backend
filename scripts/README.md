# Scripts Directory

This directory contains various scripts for development, testing, and project management.

## Directory Structure

```
scripts/
├── dev/                 # Development workflow scripts
│   ├── setup_dev.sh     # Sets up the development environment
│   ├── quality_check.sh # Runs code quality checks
│   └── migrate_to_uv.sh # Migration script for UV dependency management
├── ci/                  # CI/CD related scripts
│   └── run_tests.sh     # Runs pytest with appropriate settings
├── utils/               # Utility scripts
│   ├── analyze_conversions.py # Analyzes document conversion data
│   └── dev.js           # JavaScript development utilities
└── task-master/         # Task-master specific files
    ├── prd.txt          # Product Requirements Document
    ├── prd.md           # Markdown version of PRD
    └── example_prd.txt  # Example PRD template
```

## Usage

### Development Scripts

```bash
# Set up development environment
./scripts/dev/setup_dev.sh

# Run code quality checks
./scripts/dev/quality_check.sh

# Migrate to UV package manager
./scripts/dev/migrate_to_uv.sh
```

### CI Scripts

```bash
# Run tests
./scripts/ci/run_tests.sh
```

### Utility Scripts

```bash
# Analyze document conversions
./scripts/utils/analyze_conversions.py
```

### Task-Master

Task-master files are used for project management and task tracking. The main files are:

- `prd.txt` - The Product Requirements Document used by task-master
- `task-complexity-report.json` - Analysis of task complexity

To parse the PRD and generate tasks:

```bash
task-master parse-prd --input=scripts/task-master/prd.txt
```

## Convenience Commands

For easier access, we provide shortcuts in the `bin/` directory:

```bash
# Setup development environment
./bin/setup

# Run tests
./bin/test
```
