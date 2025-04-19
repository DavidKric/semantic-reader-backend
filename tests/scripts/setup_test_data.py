#!/usr/bin/env python3
"""
Set up the tests/data directory structure according to pytest best practices.

This script organizes test data files into a standardized structure:
- fixtures/ - Contains all test input and expected output files
  - samples/ - Contains sample files organized by type
    - simple/ - Simple document samples
    - complex/ - Complex document samples 
    - tables/ - Documents with tables
    - figures/ - Documents with figures
    - multi_column/ - Multi-column document samples
    - rtl/ - Right-to-left language document samples
    - large/ - Large document samples
    - corrupt/ - Corrupt files for testing error handling
    - invalid/ - Invalid files (non-PDF) for testing error handling
  - expected/ - Expected outputs for tests
- temp/ - Temporary directory for files created during tests
- cache/ - Cache directories for the application

Run this script from the project root:
python tests/scripts/setup_test_data.py
"""

import os
import shutil
from pathlib import Path

# Define directory paths
TEST_DIR = Path(__file__).parent.parent
TEST_DATA_DIR = TEST_DIR / "data"
TEST_FIXTURES_DIR = TEST_DATA_DIR / "fixtures"
TEST_SAMPLES_DIR = TEST_FIXTURES_DIR / "samples"
TEST_EXPECTED_DIR = TEST_FIXTURES_DIR / "expected"
TEST_TEMP_DIR = TEST_DATA_DIR / "temp"
TEST_CACHE_DIR = TEST_DATA_DIR / "cache"

# Create directories
directories = [
    TEST_FIXTURES_DIR,
    TEST_SAMPLES_DIR,
    TEST_EXPECTED_DIR,
    TEST_TEMP_DIR,
    TEST_CACHE_DIR,
]

# Create sample type directories
sample_types = ["simple", "complex", "rtl", "tables", "figures", "multi_column", "corrupt", "invalid", "large"]
for sample_type in sample_types:
    directories.append(TEST_SAMPLES_DIR / sample_type)

# Create cache subdirectories
cache_dirs = ["papermage", "papermage_docling"]
for cache_dir in cache_dirs:
    directories.append(TEST_CACHE_DIR / cache_dir)

# Create all directories
for directory in directories:
    directory.mkdir(exist_ok=True, parents=True)
    print(f"Created directory: {directory}")

# Map sample files to their new locations
old_data_dir = TEST_DATA_DIR / "data"
if old_data_dir.exists():
    # PDF mappings from old to new locations
    pdf_mapping = {
        "sample1_simple.pdf": "simple",
        "sample2_multicolumn.pdf": "multi_column",
        "sample3_scanned.pdf": "complex",
        "sample4_tables.pdf": "tables",
        "sample5_figures.pdf": "figures",
        "sample6_mixed.pdf": "complex",
        "corrupt.pdf": "corrupt"
    }
    
    # Move each PDF to its appropriate directory
    for pdf_file, folder in pdf_mapping.items():
        source = old_data_dir / pdf_file
        if source.exists():
            dest = TEST_SAMPLES_DIR / folder / pdf_file
            if not dest.exists():
                print(f"Copying {source} to {dest}")
                dest.parent.mkdir(exist_ok=True)
                shutil.copy(str(source), str(dest))
    
    # Move expected outputs
    old_expected_dir = old_data_dir / "expected"
    if old_expected_dir.exists() and old_expected_dir.is_dir():
        for json_file in old_expected_dir.glob("*.json"):
            dest = TEST_EXPECTED_DIR / json_file.name
            if not dest.exists():
                print(f"Copying {json_file} to {dest}")
                shutil.copy(str(json_file), str(dest))

# Check for files in old document directory structure
old_docs_dir = TEST_DATA_DIR / "documents"
if old_docs_dir.exists():
    for category in ["simple", "complex", "rtl", "large"]:
        old_category_dir = old_docs_dir / category
        if old_category_dir.exists() and old_category_dir.is_dir():
            for pdf_file in old_category_dir.glob("*.pdf"):
                dest = TEST_SAMPLES_DIR / category / pdf_file.name
                if not dest.exists():
                    print(f"Copying {pdf_file} to {dest}")
                    shutil.copy(str(pdf_file), str(dest))

# Copy invalid text file
invalid_text = TEST_DATA_DIR / "invalid.txt"
if invalid_text.exists():
    dest = TEST_SAMPLES_DIR / "invalid" / "invalid.txt"
    if not dest.exists():
        print(f"Copying {invalid_text} to {dest}")
        shutil.copy(str(invalid_text), str(dest))

print("\nTest data directory setup complete.")
print(f"All test data is now organized in {TEST_FIXTURES_DIR}")
print("Directory structure:")
print("├── fixtures/")
print("│   ├── samples/")
for sample_type in sorted(sample_types):
    print(f"│   │   ├── {sample_type}/")
print("│   └── expected/")
print("├── temp/")
print("└── cache/")
for cache_dir in sorted(cache_dirs):
    print(f"    └── {cache_dir}/")

print("\nUpdate tests to use this new structure by importing fixtures from conftest.py") 