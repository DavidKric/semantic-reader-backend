#!/usr/bin/env python
"""
Test runner script for semantic-reader-backend.

This script runs all the simple test scripts sequentially and reports
overall success or failure.
"""

import os
import sys
import subprocess
from pathlib import Path
import importlib.util
import time


def check_dependencies():
    """Check and install required dependencies for tests."""
    print("Checking dependencies...")
    
    # Create requirements-test.txt if it doesn't exist
    req_file = Path(__file__).parent / "tests" / "requirements-test.txt"
    if not req_file.exists():
        print("Creating test requirements file...")
        with open(req_file, "w") as f:
            f.write("""
# Test dependencies
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
""")
    
    # Install dependencies using uv instead of pip
    try:
        print("Installing test dependencies using uv...")
        subprocess.run(["uv", "pip", "install", "-r", str(req_file)], check=True)
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False


def run_test_script(script_path):
    """Run a test script and return success status."""
    print(f"\n{'='*80}")
    print(f"Running test: {script_path}")
    print(f"{'='*80}")
    
    start_time = time.time()
    try:
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
        elapsed_time = time.time() - start_time
        
        # Print output
        print(result.stdout)
        if result.stderr:
            print("ERRORS:")
            print(result.stderr)
        
        success = result.returncode == 0
        print(f"Test {'PASSED' if success else 'FAILED'} in {elapsed_time:.2f} seconds")
        return success
    except Exception as e:
        print(f"Error running test: {e}")
        return False


def main():
    """Run all test scripts."""
    print("\n📋 Semantic Reader Backend Test Runner 📋\n")
    
    # Check dependencies
    if not check_dependencies():
        print("Failed to install dependencies. Aborting tests.")
        return 1
    
    # Test scripts to run
    script_dir = Path(__file__).parent
    test_scripts = [
        script_dir / "simple_test_report.py",
        script_dir / "simple_test_visualizations.py",
        script_dir / "simple_test_service_mock.py",  # Use the mock version to avoid import errors
    ]
    
    # Add any pytest scripts you want to run
    # test_scripts.append(["pytest", "-xvs", "tests/reporting"])
    
    # Run tests
    results = []
    for script in test_scripts:
        if isinstance(script, list):
            # For pytest or other command-based tests
            cmd = script
            cmd_str = " ".join(cmd)
            print(f"\n{'='*80}")
            print(f"Running: {cmd_str}")
            print(f"{'='*80}")
            try:
                result = subprocess.run(cmd, check=False)
                success = result.returncode == 0
                results.append((cmd_str, success))
            except Exception as e:
                print(f"Error running command: {e}")
                results.append((cmd_str, False))
        else:
            # For Python scripts
            success = run_test_script(script)
            results.append((script.name, success))
    
    # Print summary
    print("\n\n📊 Test Summary 📊")
    print("=" * 60)
    all_passed = True
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")
        if not success:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed successfully! 🎉")
        return 0
    else:
        print("❗ Some tests failed. Please check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 