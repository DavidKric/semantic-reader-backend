#!/usr/bin/env python3
"""
Test script to verify the API endpoints work with the new Docling converter.
"""

import json
import sys
import time
from pathlib import Path

import requests

# Add the src directory to Python path
src_path = Path(__file__).resolve().parents[2] / "src"
sys.path.append(str(src_path))

def find_sample_pdf():
    """Find a sample PDF file to test with."""
    # Look in common directories for a PDF file
    search_dirs = [
        Path("examples"),
        Path("tests/fixtures"),
        Path("tests/data"),
        Path("tests"),
        Path("docs"),
        Path("."),
    ]
    
    for directory in search_dirs:
        if not directory.exists():
            continue
        
        for file in directory.glob("**/*.pdf"):
            print(f"Found sample PDF: {file}")
            return file
    
    print("No sample PDF found. Please provide a PDF file path to test with.")
    return None

def test_api_gateway():
    """
    Test the API gateway using direct import.
    This verifies that the new converter works when called via the API gateway.
    """
    try:
        from papermage_docling.api.gateway import process_document
        print("Testing API gateway...")
        
        pdf_path = find_sample_pdf()
        if pdf_path is None:
            print("⚠️ Skipping gateway test: No PDF file found")
            return
        
        options = {
            "detect_tables": True,
            "detect_figures": True,
            "enable_ocr": False
        }
        
        result = process_document(str(pdf_path), options=options)
        
        # Verify basic structure
        assert "id" in result, "Missing 'id' in result"
        assert "pages" in result, "Missing 'pages' in result"
        assert isinstance(result["pages"], list), "'pages' is not a list"
        assert "metadata" in result, "Missing 'metadata' in result"
        
        print(f"✅ API gateway test passed! Result has {len(result['pages'])} pages")
        return True
    except Exception as e:
        print(f"❌ API gateway test failed: {e}")
        return False

def test_papermage_api():
    """
    Test the PaperMage API using direct import.
    This verifies that the new converter works when called via the PaperMage API.
    """
    try:
        from papermage_docling.api.papermage import process_document
        print("Testing PaperMage API...")
        
        pdf_path = find_sample_pdf()
        if pdf_path is None:
            print("⚠️ Skipping PaperMage API test: No PDF file found")
            return
        
        options = {
            "detect_tables": True,
            "detect_figures": True,
            "enable_ocr": False
        }
        
        result = process_document(str(pdf_path), options=options)
        
        # Verify basic structure
        assert "version" in result, "Missing 'version' in result"
        assert "document" in result, "Missing 'document' in result"
        assert "pages" in result["document"], "Missing 'pages' in document"
        
        print(f"✅ PaperMage API test passed! Result has {len(result['document']['pages'])} pages")
        return True
    except Exception as e:
        print(f"❌ PaperMage API test failed: {e}")
        return False

def test_recipe_api_server():
    """
    Test the Recipe API endpoints by starting a test server.
    This requires the API server to be running.
    """
    try:
        print("Note: This test requires the API server to be running.")
        print("You should start the server in another terminal with: uvicorn app.main:app --reload")
        
        server_url = input("Enter server URL (press Enter for http://localhost:8000): ").strip() or "http://localhost:8000"
        
        pdf_path = find_sample_pdf()
        if pdf_path is None:
            print("⚠️ Skipping Recipe API test: No PDF file found")
            return False
        
        # Test the /recipe/process endpoint
        print("Testing /recipe/process endpoint...")
        url = f"{server_url}/recipe/process"
        
        with open(pdf_path, "rb") as f:
            options = json.dumps({
                "detect_tables": True,
                "detect_figures": True,
                "enable_ocr": False
            })
            files = {"file": (pdf_path.name, f, "application/pdf")}
            data = {"options": options}
            
            response = requests.post(url, files=files, data=data)
        
        if response.status_code != 200:
            print(f"❌ Recipe API test failed: {response.status_code} {response.text}")
            return False
        
        job_id = response.json().get("job_id")
        if not job_id:
            print("❌ Recipe API test failed: No job_id in response")
            return False
        
        print(f"Job ID: {job_id}, waiting for processing to complete...")
        
        # Poll the /recipe/result endpoint until processing is complete
        result_url = f"{server_url}/recipe/result/{job_id}"
        max_retries = 10
        retry_count = 0
        
        while retry_count < max_retries:
            response = requests.get(result_url)
            if response.status_code != 200:
                print(f"❌ Recipe API test failed: {response.status_code} {response.text}")
                return False
            
            result = response.json()
            if result.get("status") == "completed":
                print("Processing completed!")
                
                # Verify result structure
                assert "result" in result, "Missing 'result' in response"
                
                doc_result = result["result"]
                print("✅ Recipe API test passed! Result has document data")
                return True
            
            if result.get("status") == "error":
                print(f"❌ Recipe API test failed: Processing error: {result.get('result', {}).get('error')}")
                return False
            
            print("Processing still in progress, retrying in 1 second...")
            time.sleep(1)
            retry_count += 1
        
        print("❌ Recipe API test failed: Processing timed out")
        return False
    except Exception as e:
        print(f"❌ Recipe API test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Semantic Reader API with new Docling converter...")
    
    gateway_success = test_api_gateway()
    papermage_success = test_papermage_api()
    
    # This test is optional as it requires the server to be running
    run_server_test = input("\nRun Recipe API server test? (y/N): ").strip().lower()
    recipe_success = test_recipe_api_server() if run_server_test == 'y' else None
    
    print("\nTest Summary:")
    print(f"API Gateway Test: {'✅ Passed' if gateway_success else '❌ Failed'}")
    print(f"PaperMage API Test: {'✅ Passed' if papermage_success else '❌ Failed'}")
    
    if recipe_success is not None:
        print(f"Recipe API Test: {'✅ Passed' if recipe_success else '❌ Failed'}")
    else:
        print("Recipe API Test: ⚠️ Skipped")
    
    if gateway_success and papermage_success and (recipe_success is None or recipe_success):
        print("\n✅ All tested components are working correctly!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Check the output for details.")
        sys.exit(1) 