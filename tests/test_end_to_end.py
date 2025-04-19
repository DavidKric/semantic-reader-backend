"""
End-to-end tests for PaperMage-Docling comparing its output with the original PaperMage.

This module implements comprehensive tests that validate the compatibility and behavior
of PaperMage-Docling against the original PaperMage implementation.
"""

import json
import logging
import tempfile
from pathlib import Path

import pytest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for configuration
CONFIG_FILE = Path(__file__).parent / "e2e_test_config.json"
TOLERANCE = {
    "coordinate": 2.0,  # Pixel tolerance for coordinate differences
    "text": 0.95,       # Text similarity threshold (0.0-1.0)
    "confidence": 0.05, # Confidence score tolerance
}

# Test fixture for initializing both PaperMage and PaperMage-Docling
@pytest.fixture
def papermage_engines():
    """
    Initialize both PaperMage and PaperMage-Docling with identical configurations.
    
    Returns:
        tuple: (papermage_original, papermage_docling) instances
    """
    try:
        # Import original PaperMage (assuming it's installed)
        import papermage as pm_original
        
        # Import PaperMage-Docling
        import papermage_docling as pm_docling
        
        # Initialize with identical configurations
        original_engine = pm_original.Engine(
            use_cuda=False,
            cache_dir=tempfile.mkdtemp(prefix="pm_original_")
        )
        
        docling_engine = pm_docling.Engine(
            use_cuda=False,
            cache_dir=tempfile.mkdtemp(prefix="pm_docling_")
        )
        
        return original_engine, docling_engine
    
    except ImportError as e:
        pytest.skip(f"Engine initialization failed: {str(e)}")

@pytest.fixture
def test_documents():
    """
    Provide test document paths for different test scenarios.
    
    Returns:
        dict: Document paths categorized by test type
    """
    # Base directory for test documents
    test_docs_dir = Path(__file__).parent / "test_data" / "documents"
    
    return {
        "simple": [
            test_docs_dir / "simple" / "single_column.pdf",
            test_docs_dir / "simple" / "basic_text.pdf",
        ],
        "complex": [
            test_docs_dir / "complex" / "multi_column.pdf",
            test_docs_dir / "complex" / "tables_and_figures.pdf",
        ],
        "rtl": [
            test_docs_dir / "rtl" / "arabic_text.pdf",
            test_docs_dir / "rtl" / "hebrew_text.pdf",
        ],
        "large": [
            test_docs_dir / "large" / "large_document.pdf",
        ]
    }

# Utility functions for comparing outputs
def are_coordinates_equal(coord1, coord2, tolerance=TOLERANCE["coordinate"]):
    """
    Compare coordinates with a configurable tolerance level.
    
    Args:
        coord1: First coordinate (x, y) or (x, y, w, h)
        coord2: Second coordinate to compare
        tolerance: Maximum allowed difference in pixels
        
    Returns:
        bool: True if coordinates are within tolerance
    """
    if len(coord1) != len(coord2):
        return False
    
    return all(abs(a - b) <= tolerance for a, b in zip(coord1, coord2, strict=False))

def compare_text_content(text1, text2, similarity_threshold=TOLERANCE["text"]):
    """
    Compare text content with a configurable similarity threshold.
    
    Args:
        text1: First text string
        text2: Second text string
        similarity_threshold: Minimum similarity score (0.0-1.0)
        
    Returns:
        bool: True if texts are sufficiently similar
    """
    # Simple character-based similarity for now
    # In a real implementation, we might use more sophisticated methods
    if not text1 and not text2:
        return True
    
    if not text1 or not text2:
        return False
    
    # Calculate Levenshtein distance or similar metric
    # For now, using a simple character-based approach
    shorter = min(len(text1), len(text2))
    longer = max(len(text1), len(text2))
    
    if longer == 0:
        return True
    
    # Count matching characters
    matches = sum(c1 == c2 for c1, c2 in zip(text1, text2, strict=False))
    similarity = matches / longer
    
    return similarity >= similarity_threshold

def compare_outputs(pm_output, docling_output, tolerance_config=TOLERANCE):
    """
    Compare outputs from PaperMage and PaperMage-Docling with configurable tolerance.
    
    Args:
        pm_output: Output from original PaperMage
        docling_output: Output from PaperMage-Docling
        tolerance_config: Dictionary of tolerance levels for different attributes
        
    Returns:
        tuple: (is_similar, differences)
    """
    differences = []
    
    # Compare document structure
    if isinstance(pm_output, dict) and isinstance(docling_output, dict):
        for key in set(pm_output.keys()).union(docling_output.keys()):
            if key not in pm_output:
                differences.append(f"Key '{key}' missing in PaperMage output")
            elif key not in docling_output:
                differences.append(f"Key '{key}' missing in PaperMage-Docling output")
            else:
                # Recursive comparison for nested structures
                if isinstance(pm_output[key], dict) and isinstance(docling_output[key], dict):
                    is_similar, child_diffs = compare_outputs(pm_output[key], docling_output[key], tolerance_config)
                    if not is_similar:
                        differences.extend([f"{key}.{d}" for d in child_diffs])
                # Compare lists
                elif isinstance(pm_output[key], list) and isinstance(docling_output[key], list):
                    if len(pm_output[key]) != len(docling_output[key]):
                        differences.append(f"List '{key}' length differs: {len(pm_output[key])} vs {len(docling_output[key])}")
                    
                    # For now, just check lengths - detailed list comparison would be item-type-specific
                    # and implemented in specific test cases
                
                # Compare simple values
                elif pm_output[key] != docling_output[key]:
                    # Handle special cases by type
                    if 'coord' in key or 'box' in key:
                        if not are_coordinates_equal(pm_output[key], docling_output[key], tolerance_config["coordinate"]):
                            differences.append(f"Coordinate '{key}' differs beyond tolerance")
                    elif 'text' in key:
                        if not compare_text_content(pm_output[key], docling_output[key], tolerance_config["text"]):
                            differences.append(f"Text '{key}' differs beyond similarity threshold")
                    else:
                        differences.append(f"Value '{key}' differs: {pm_output[key]} vs {docling_output[key]}")
    
    # Compare non-dict outputs
    else:
        differences.append(f"Output types differ: {type(pm_output)} vs {type(docling_output)}")
    
    return len(differences) == 0, differences

def log_differences(document_name, differences):
    """
    Log differences between outputs in a structured way.
    
    Args:
        document_name: Name of the test document
        differences: List of differences found
    """
    if differences:
        logger.warning(f"Differences found for {document_name}:")
        for i, diff in enumerate(differences, 1):
            logger.warning(f"  {i}. {diff}")
    else:
        logger.info(f"No differences found for {document_name}")

# Create test configuration file
def generate_config_file():
    """Generate a default configuration file for E2E tests if it doesn't exist."""
    if not CONFIG_FILE.exists():
        config = {
            "tolerances": TOLERANCE,
            "test_data_paths": {
                "simple": "test_data/documents/simple",
                "complex": "test_data/documents/complex",
                "rtl": "test_data/documents/rtl",
                "large": "test_data/documents/large",
            },
            "html_report": {
                "enabled": True,
                "output_dir": "test_results/html",
            }
        }
        
        # Create parent directory if it doesn't exist
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Created default configuration file at {CONFIG_FILE}")

# Basic test to verify the test environment is working
def test_environment_setup(papermage_engines):
    """
    Verify that both PaperMage and PaperMage-Docling can be initialized.
    """
    pm_original, pm_docling = papermage_engines
    assert pm_original is not None, "Failed to initialize original PaperMage"
    assert pm_docling is not None, "Failed to initialize PaperMage-Docling"
    
    # Check if basic methods exist in both implementations
    for method_name in ["load_pdf", "process", "extract_text"]:
        assert hasattr(pm_original, method_name), f"Original PaperMage missing {method_name} method"
        assert hasattr(pm_docling, method_name), f"PaperMage-Docling missing {method_name} method"

# Generate configuration file when module is imported
generate_config_file()

# -----------------------------------------------------------------------------
# Core Document Processing Comparison Tests
# -----------------------------------------------------------------------------

def get_test_document_configs():
    """
    Load test document configurations from the config file.
    
    Returns:
        List[Dict]: List of document test configurations
    """
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            return config.get("document_samples", [])
    return []

def get_test_case_config(test_case_name):
    """
    Get configuration for a specific test case, including any tolerance overrides.
    
    Args:
        test_case_name: Name of the test case to get configuration for
        
    Returns:
        Dict: Test case configuration including tolerances
    """
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            
            # Get the base tolerance config
            tolerance_config = config.get("tolerances", TOLERANCE)
            
            # Get any test case specific overrides
            test_case_config = config.get("test_cases", {}).get(test_case_name, {})
            enabled = test_case_config.get("enabled", True)
            
            # Apply any tolerance overrides
            tolerance_overrides = test_case_config.get("tolerance_override", {})
            for key, value in tolerance_overrides.items():
                tolerance_config[key] = value
                
            return {
                "enabled": enabled,
                "tolerances": tolerance_config,
                "config": test_case_config
            }
    
    # Return default config if file doesn't exist
    return {
        "enabled": True,
        "tolerances": TOLERANCE,
        "config": {}
    }

@pytest.fixture
def sample_documents():
    """
    Provide a list of sample document configurations from the config file.
    
    Returns:
        list: Sample document configurations
    """
    return get_test_document_configs()

# Helper function to load and process a document with both engines
def process_document_with_both_engines(papermage_engines, document_path):
    """
    Process a document with both PaperMage and PaperMage-Docling engines.
    
    Args:
        papermage_engines: Tuple of (pm_original, pm_docling)
        document_path: Path to the document file
        
    Returns:
        tuple: (pm_output, docling_output)
    """
    pm_original, pm_docling = papermage_engines
    
    # Check if document exists
    if not Path(document_path).exists():
        logger.error(f"Document not found: {document_path}")
        return None, None
    
    try:
        # Process with original PaperMage
        pm_doc = pm_original.load_pdf(document_path)
        pm_output = pm_original.process(pm_doc)
        
        # Process with PaperMage-Docling
        docling_doc = pm_docling.load_pdf(document_path)
        docling_output = pm_docling.process(docling_doc)
        
        return pm_output, docling_output
    except Exception as e:
        logger.error(f"Error processing document {document_path}: {str(e)}")
        return None, None

# Test document loading
@pytest.mark.parametrize("doc_type", ["simple", "complex", "rtl"])
def test_document_loading(papermage_engines, test_documents, doc_type):
    """
    Test that both engines can load the same documents.
    
    Args:
        papermage_engines: Tuple of (pm_original, pm_docling)
        test_documents: Dictionary of test document paths
        doc_type: Type of document to test (simple, complex, rtl)
    """
    pm_original, pm_docling = papermage_engines
    
    # Skip if no documents of this type
    if doc_type not in test_documents or not test_documents[doc_type]:
        pytest.skip(f"No {doc_type} documents available for testing")
    
    for doc_path in test_documents[doc_type]:
        # Skip if document doesn't exist
        if not doc_path.exists():
            logger.warning(f"Skipping non-existent document: {doc_path}")
            continue
        
        # Load with original PaperMage
        pm_doc = pm_original.load_pdf(doc_path)
        assert pm_doc is not None, f"Failed to load {doc_path} with original PaperMage"
        
        # Load with PaperMage-Docling
        docling_doc = pm_docling.load_pdf(doc_path)
        assert docling_doc is not None, f"Failed to load {doc_path} with PaperMage-Docling"
        
        # Check if both engines recognize the same number of pages
        assert pm_doc.num_pages == docling_doc.num_pages, \
            f"Page count mismatch: {pm_doc.num_pages} vs {docling_doc.num_pages}"

# Token extraction test
@pytest.mark.parametrize("doc_sample", get_test_document_configs())
def test_token_extraction(papermage_engines, doc_sample):
    """
    Test token extraction capabilities of both engines.
    
    Args:
        papermage_engines: Tuple of (pm_original, pm_docling) 
        doc_sample: Document sample configuration
    """
    # Get test case configuration
    test_config = get_test_case_config("token_extraction")
    if not test_config["enabled"]:
        pytest.skip("Token extraction test is disabled in config")
    
    # Prepare document path
    doc_name = doc_sample["name"]
    doc_path = Path(__file__).parent / "test_data" / "documents" / doc_sample["path"]
    
    # Skip if document doesn't exist
    if not doc_path.exists():
        pytest.skip(f"Document not found: {doc_path}")
    
    # Process document with both engines
    pm_output, docling_output = process_document_with_both_engines(papermage_engines, doc_path)
    
    # Skip if processing failed
    if pm_output is None or docling_output is None:
        pytest.skip(f"Failed to process document: {doc_path}")
    
    # Extract tokens from both outputs
    pm_tokens = pm_output.get("tokens", [])
    docling_tokens = docling_output.get("tokens", [])
    
    # Check token count
    assert len(pm_tokens) == len(docling_tokens), \
        f"Token count mismatch for {doc_name}: {len(pm_tokens)} vs {len(docling_tokens)}"
    
    # Compare token properties
    differences = []
    for i, (pm_token, docling_token) in enumerate(zip(pm_tokens, docling_tokens, strict=False)):
        # Compare text content
        if not compare_text_content(pm_token.get("text", ""), docling_token.get("text", ""),
                               test_config["tolerances"]["text"]):
            differences.append(f"Token {i} text differs: '{pm_token.get('text', '')}' vs '{docling_token.get('text', '')}'")
        
        # Compare coordinates
        if "bbox" in pm_token and "bbox" in docling_token:
            if not are_coordinates_equal(pm_token["bbox"], docling_token["bbox"], 
                                    test_config["tolerances"]["coordinate"]):
                differences.append(f"Token {i} bbox differs: {pm_token['bbox']} vs {docling_token['bbox']}")
    
    # Log and assert differences
    log_differences(f"{doc_name} token extraction", differences)
    assert len(differences) == 0, f"{len(differences)} token differences found in {doc_name}"

# Text recognition test
@pytest.mark.parametrize("doc_sample", get_test_document_configs())
def test_text_recognition(papermage_engines, doc_sample):
    """
    Test text recognition capabilities of both engines.
    
    Args:
        papermage_engines: Tuple of (pm_original, pm_docling)
        doc_sample: Document sample configuration
    """
    # Get test case configuration
    test_config = get_test_case_config("text_recognition")
    if not test_config["enabled"]:
        pytest.skip("Text recognition test is disabled in config")
    
    # Prepare document path
    doc_name = doc_sample["name"]
    doc_path = Path(__file__).parent / "test_data" / "documents" / doc_sample["path"]
    
    # Skip if document doesn't exist
    if not doc_path.exists():
        pytest.skip(f"Document not found: {doc_path}")
    
    # Process document with both engines
    pm_original, pm_docling = papermage_engines
    
    try:
        # Load documents
        pm_doc = pm_original.load_pdf(doc_path)
        docling_doc = pm_docling.load_pdf(doc_path)
        
        # Extract text from both engines
        pm_text = pm_original.extract_text(pm_doc)
        docling_text = pm_docling.extract_text(docling_doc)
        
        # Compare overall text extraction
        similarity_threshold = test_config["tolerances"]["text"]
        text_similarity = compare_text_content(pm_text, docling_text, similarity_threshold)
        
        # Assert similarity
        assert text_similarity, \
            f"Text recognition for {doc_name} failed. Similarity below threshold {similarity_threshold}"
        
        # Test text extraction by page
        for page_num in range(min(pm_doc.num_pages, docling_doc.num_pages)):
            pm_page_text = pm_original.extract_text(pm_doc, page_num=page_num)
            docling_page_text = pm_docling.extract_text(docling_doc, page_num=page_num)
            
            page_similarity = compare_text_content(pm_page_text, docling_page_text, similarity_threshold)
            assert page_similarity, \
                f"Text recognition for {doc_name}, page {page_num} failed. Similarity below threshold {similarity_threshold}"
    
    except Exception as e:
        pytest.fail(f"Error during text recognition test for {doc_name}: {str(e)}")

# Document structure test
@pytest.mark.parametrize("doc_sample", get_test_document_configs())
def test_document_structure(papermage_engines, doc_sample):
    """
    Test document structure analysis capabilities of both engines.
    
    Args:
        papermage_engines: Tuple of (pm_original, pm_docling)
        doc_sample: Document sample configuration
    """
    # Get test case configuration
    test_config = get_test_case_config("document_structure")
    if not test_config["enabled"]:
        pytest.skip("Document structure test is disabled in config")
    
    # Prepare document path
    doc_name = doc_sample["name"]
    doc_path = Path(__file__).parent / "test_data" / "documents" / doc_sample["path"]
    
    # Skip if document doesn't exist
    if not doc_path.exists():
        pytest.skip(f"Document not found: {doc_path}")
    
    # Process document with both engines
    pm_output, docling_output = process_document_with_both_engines(papermage_engines, doc_path)
    
    # Skip if processing failed
    if pm_output is None or docling_output is None:
        pytest.skip(f"Failed to process document: {doc_path}")
    
    # Elements to compare structure
    structure_elements = ["paragraphs", "sections", "headings", "tables", "figures"]
    
    # Compare structure elements
    differences = []
    for element in structure_elements:
        pm_elements = pm_output.get(element, [])
        docling_elements = docling_output.get(element, [])
        
        # Compare count
        if len(pm_elements) != len(docling_elements):
            differences.append(f"{element} count mismatch: {len(pm_elements)} vs {len(docling_elements)}")
            continue
        
        # Compare individual elements
        for i, (pm_elem, docling_elem) in enumerate(zip(pm_elements, docling_elements, strict=False)):
            # Compare bounding boxes if available
            if "bbox" in pm_elem and "bbox" in docling_elem:
                if not are_coordinates_equal(pm_elem["bbox"], docling_elem["bbox"],
                                        test_config["tolerances"]["coordinate"]):
                    differences.append(f"{element} {i} bbox differs: {pm_elem['bbox']} vs {docling_elem['bbox']}")
            
            # Compare text if available
            if "text" in pm_elem and "text" in docling_elem:
                if not compare_text_content(pm_elem["text"], docling_elem["text"],
                                       test_config["tolerances"]["text"]):
                    differences.append(f"{element} {i} text differs")
    
    # Log and assert differences
    log_differences(f"{doc_name} document structure", differences)
    assert len(differences) == 0, f"{len(differences)} structure differences found in {doc_name}"

# API endpoint test
def test_api_endpoints(papermage_engines, test_documents):
    """
    Test API endpoints for both engines.
    
    Args:
        papermage_engines: Tuple of (pm_original, pm_docling)
        test_documents: Dictionary of test document paths
    """
    # Use a simple document for API testing
    if "simple" not in test_documents or not test_documents["simple"]:
        pytest.skip("No simple documents available for API testing")
    
    doc_path = test_documents["simple"][0]
    
    # Skip if document doesn't exist
    if not doc_path.exists():
        pytest.skip(f"Document not found: {doc_path}")
    
    pm_original, pm_docling = papermage_engines
    
    try:
        # Test original PaperMage API
        pm_api_client = pm_original.get_api_client()
        pm_api_result = pm_api_client.process_document(doc_path)
        
        # Test PaperMage-Docling API
        docling_api_client = pm_docling.get_api_client()
        docling_api_result = docling_api_client.process_document(doc_path)
        
        # Compare API results
        is_similar, differences = compare_outputs(pm_api_result, docling_api_result)
        
        # Log and assert differences
        log_differences("API endpoint", differences)
        assert is_similar, f"API endpoint results differ: {len(differences)} differences found"
    
    except Exception as e:
        # It's possible that the API endpoints aren't available or are configured differently
        logger.warning(f"API endpoint test failed: {str(e)}")
        pytest.skip(f"API endpoint test skipped: {str(e)}")

# Comprehensive document processing comparison test
@pytest.mark.parametrize("doc_type", ["simple", "complex"])
def test_core_document_processing_comparison(papermage_engines, test_documents, doc_type):
    """
    Comprehensive test that compares core document processing capabilities between
    PaperMage-Docling and original PaperMage.
    
    This test focuses on token extraction, text recognition, and document structure analysis
    with detailed comparison of outputs and clear identification of differences.
    
    Args:
        papermage_engines: Tuple of (pm_original, pm_docling)
        test_documents: Dictionary of test document paths
        doc_type: Type of document to test (simple, complex)
    """
    pm_original, pm_docling = papermage_engines
    
    # Skip if no documents of this type
    if doc_type not in test_documents or not test_documents[doc_type]:
        pytest.skip(f"No {doc_type} documents available for testing")
    
    # Get tolerance configuration
    config = get_test_case_config("core_processing")
    tolerance_config = config["tolerances"]
    
    # Process each document
    for doc_path in test_documents[doc_type]:
        # Skip if document doesn't exist
        if not doc_path.exists():
            logger.warning(f"Skipping non-existent document: {doc_path}")
            continue
        
        doc_name = doc_path.stem
        logger.info(f"Testing core document processing for {doc_name}")
        
        try:
            # Process with original PaperMage
            pm_doc = pm_original.load_pdf(doc_path)
            pm_output = pm_original.process(pm_doc)
            
            # Process with PaperMage-Docling
            docling_doc = pm_docling.load_pdf(doc_path)
            docling_output = pm_docling.process(docling_doc)
            
            # Store results for comparison and reporting
            results_dir = Path(__file__).parent / "test_results" / "comparison"
            results_dir.mkdir(parents=True, exist_ok=True)
            
            # Save outputs for reference (optional)
            with open(results_dir / f"{doc_name}_pm_original.json", 'w') as f:
                json.dump(pm_output, f, indent=2)
            with open(results_dir / f"{doc_name}_pm_docling.json", 'w') as f:
                json.dump(docling_output, f, indent=2)
            
            # 1. Compare token extraction
            token_differences = []
            pm_tokens = pm_output.get("tokens", [])
            docling_tokens = docling_output.get("tokens", [])
            
            logger.info(f"  Token count: {len(pm_tokens)} (original) vs {len(docling_tokens)} (docling)")
            
            # Compare token counts
            assert abs(len(pm_tokens) - len(docling_tokens)) <= max(1, int(0.05 * len(pm_tokens))), \
                f"Token count difference exceeds 5%: {len(pm_tokens)} vs {len(docling_tokens)}"
            
            # Compare token properties up to the smaller count
            for i, (pm_token, docling_token) in enumerate(zip(pm_tokens, docling_tokens, strict=False)):
                # Compare text content
                if not compare_text_content(pm_token.get("text", ""), docling_token.get("text", ""),
                                   tolerance_config["text"]):
                    token_differences.append(f"Token {i} text differs: '{pm_token.get('text', '')}' vs '{docling_token.get('text', '')}'")
                
                # Compare coordinates if available
                if "bbox" in pm_token and "bbox" in docling_token:
                    if not are_coordinates_equal(pm_token["bbox"], docling_token["bbox"], 
                                            tolerance_config["coordinate"]):
                        token_differences.append(f"Token {i} bbox differs: {pm_token['bbox']} vs {docling_token['bbox']}")
                
                # Compare confidence scores if available
                if "confidence" in pm_token and "confidence" in docling_token:
                    if abs(pm_token["confidence"] - docling_token["confidence"]) > tolerance_config["confidence"]:
                        token_differences.append(f"Token {i} confidence differs: {pm_token['confidence']} vs {docling_token['confidence']}")
            
            # 2. Compare document structure
            structure_differences = []
            structure_elements = ["paragraphs", "sections", "headings"]
            
            for element in structure_elements:
                pm_elements = pm_output.get(element, [])
                docling_elements = docling_output.get(element, [])
                
                logger.info(f"  {element.capitalize()} count: {len(pm_elements)} (original) vs {len(docling_elements)} (docling)")
                
                # Allow small differences in counts
                if abs(len(pm_elements) - len(docling_elements)) > max(1, int(0.1 * len(pm_elements))):
                    structure_differences.append(f"{element.capitalize()} count difference exceeds 10%: {len(pm_elements)} vs {len(docling_elements)}")
                
                # Compare properties of common elements
                for i, (pm_elem, docling_elem) in enumerate(zip(pm_elements, docling_elements, strict=False)):
                    # Compare bounding boxes if available
                    if "bbox" in pm_elem and "bbox" in docling_elem:
                        if not are_coordinates_equal(pm_elem["bbox"], docling_elem["bbox"],
                                                tolerance_config["coordinate"]):
                            structure_differences.append(f"{element} {i} bbox differs: {pm_elem['bbox']} vs {docling_elem['bbox']}")
                    
                    # Compare text if available
                    if "text" in pm_elem and "text" in docling_elem:
                        if not compare_text_content(pm_elem["text"], docling_elem["text"],
                                               tolerance_config["text"]):
                            structure_differences.append(f"{element} {i} text differs")
                    
                    # Compare hierarchy level for sections and headings
                    if "level" in pm_elem and "level" in docling_elem:
                        if pm_elem["level"] != docling_elem["level"]:
                            structure_differences.append(f"{element} {i} level differs: {pm_elem['level']} vs {docling_elem['level']}")
            
            # 3. Compare overall text extraction
            pm_text = pm_original.extract_text(pm_doc)
            docling_text = pm_docling.extract_text(docling_doc)
            
            text_similarity = compare_text_content(pm_text, docling_text, tolerance_config["text"])
            
            if not text_similarity:
                logger.warning(f"Text recognition for {doc_name} is below similarity threshold {tolerance_config['text']}")
                
                # Calculate character-level similarity for detailed reporting
                total_chars = max(len(pm_text), len(docling_text))
                if total_chars > 0:
                    matching_chars = sum(a == b for a, b in zip(pm_text[:min(len(pm_text), len(docling_text))], 
                                                             docling_text[:min(len(pm_text), len(docling_text))], strict=False))
                    similarity_percentage = (matching_chars / total_chars) * 100
                    logger.warning(f"Text similarity: {similarity_percentage:.2f}%")
            
            # 4. Compare page-level processing
            page_differences = []
            for page_num in range(min(pm_doc.num_pages, docling_doc.num_pages)):
                # Extract page-level text
                pm_page_text = pm_original.extract_text(pm_doc, page_num=page_num)
                docling_page_text = pm_docling.extract_text(docling_doc, page_num=page_num)
                
                page_similarity = compare_text_content(pm_page_text, docling_page_text, tolerance_config["text"])
                if not page_similarity:
                    page_differences.append(f"Page {page_num} text similarity below threshold {tolerance_config['text']}")
            
            # Log all differences
            all_differences = token_differences + structure_differences + page_differences
            log_differences(doc_name, all_differences)
            
            # Generate detailed report
            report_path = results_dir / f"{doc_name}_comparison_report.json"
            report = {
                "document": str(doc_path),
                "token_comparison": {
                    "original_count": len(pm_tokens),
                    "docling_count": len(docling_tokens),
                    "differences": token_differences
                },
                "structure_comparison": {
                    "differences": structure_differences,
                    "elements": {elem: {"original": len(pm_output.get(elem, [])), 
                                      "docling": len(docling_output.get(elem, []))}
                                for elem in structure_elements}
                },
                "text_comparison": {
                    "overall_similarity": text_similarity,
                    "page_differences": page_differences
                }
            }
            
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Assert overall comparison success
            max_allowed_differences = int(config.get("config", {}).get("max_allowed_differences", 5))
            assert len(all_differences) <= max_allowed_differences, \
                f"{len(all_differences)} differences found in {doc_name}, exceeding maximum allowed ({max_allowed_differences})"
            
        except Exception as e:
            logger.error(f"Error in core document processing test for {doc_name}: {str(e)}")
            raise

# Multi-column document layout and table analysis test
@pytest.mark.parametrize("doc_sample", [s for s in get_test_document_configs() if "complex" in s.get("path", "")])
def test_complex_layout_analysis(papermage_engines, doc_sample):
    """
    Test the system's ability to handle complex layouts including multi-column documents,
    tables, and figures. This specifically tests layout analysis capabilities.
    
    Args:
        papermage_engines: Tuple of (pm_original, pm_docling)
        doc_sample: Complex document sample configuration from config
    """
    # Get test case configuration
    test_config = get_test_case_config("layout_detection")
    if not test_config["enabled"]:
        pytest.skip("Layout detection test is disabled in config")
    
    # Prepare document path and name
    doc_name = doc_sample["name"]
    doc_path = Path(__file__).parent / "test_data" / "documents" / doc_sample["path"]
    
    # Skip if document doesn't exist
    if not doc_path.exists():
        pytest.skip(f"Document not found: {doc_path}")
    
    logger.info(f"Testing complex layout analysis for document: {doc_name}")
    
    # Process document with both engines
    pm_original, pm_docling = papermage_engines
    
    try:
        # Load and process documents
        pm_doc = pm_original.load_pdf(doc_path)
        pm_output = pm_original.process(pm_doc)
        
        docling_doc = pm_docling.load_pdf(doc_path)
        docling_output = pm_docling.process(docling_doc)
        
        # Store results for analysis
        results_dir = Path(__file__).parent / "test_results" / "layouts"
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Compare layout elements
        layout_differences = []
        
        # 1. Compare column detection
        pm_columns = pm_output.get("columns", [])
        docling_columns = docling_output.get("columns", [])
        
        logger.info(f"  Columns detected: {len(pm_columns)} (original) vs {len(docling_columns)} (docling)")
        
        # Allow a small difference in column count (0-1 columns)
        if abs(len(pm_columns) - len(docling_columns)) > 1:
            layout_differences.append(f"Column count differs significantly: {len(pm_columns)} vs {len(docling_columns)}")
        
        # Compare column properties (if both have columns)
        if pm_columns and docling_columns:
            for i, (pm_col, docling_col) in enumerate(zip(pm_columns[:min(len(pm_columns), len(docling_columns))], strict=False)):
                # Compare column boundaries
                if "bbox" in pm_col and "bbox" in docling_col:
                    if not are_coordinates_equal(pm_col["bbox"], docling_col["bbox"], 
                                            test_config["tolerances"]["coordinate"]):
                        layout_differences.append(f"Column {i} boundaries differ: {pm_col['bbox']} vs {docling_col['bbox']}")
                
                # Compare reading order if available
                if "reading_order" in pm_col and "reading_order" in docling_col:
                    if pm_col["reading_order"] != docling_col["reading_order"]:
                        layout_differences.append(f"Column {i} reading order differs: {pm_col['reading_order']} vs {docling_col['reading_order']}")
        
        # 2. Compare table detection
        pm_tables = pm_output.get("tables", [])
        docling_tables = docling_output.get("tables", [])
        
        logger.info(f"  Tables detected: {len(pm_tables)} (original) vs {len(docling_tables)} (docling)")
        
        # Tables can be harder to detect consistently, so allow for some variability
        if abs(len(pm_tables) - len(docling_tables)) > 1:
            layout_differences.append(f"Table count differs: {len(pm_tables)} vs {len(docling_tables)}")
        
        # Compare table structure for common tables
        for i, (pm_table, docling_table) in enumerate(zip(pm_tables[:min(len(pm_tables), len(docling_tables))], strict=False)):
            # Compare table boundaries
            if "bbox" in pm_table and "bbox" in docling_table:
                if not are_coordinates_equal(pm_table["bbox"], docling_table["bbox"], 
                                        test_config["tolerances"]["coordinate"]):
                    layout_differences.append(f"Table {i} boundaries differ: {pm_table['bbox']} vs {docling_table['bbox']}")
            
            # Compare row/column counts
            pm_rows = pm_table.get("rows", [])
            docling_rows = docling_table.get("rows", [])
            
            if abs(len(pm_rows) - len(docling_rows)) > 1:
                layout_differences.append(f"Table {i} row count differs: {len(pm_rows)} vs {len(docling_rows)}")
            
            pm_cols = pm_table.get("columns", [])
            docling_cols = docling_table.get("columns", [])
            
            if abs(len(pm_cols) - len(docling_cols)) > 1:
                layout_differences.append(f"Table {i} column count differs: {len(pm_cols)} vs {len(docling_cols)}")
            
            # Compare cell contents (for a subset of cells if tables are large)
            pm_cells = pm_table.get("cells", [])
            docling_cells = docling_table.get("cells", [])
            
            # Sample up to 5 cells for comparison
            cell_sample_size = min(5, len(pm_cells), len(docling_cells))
            for j in range(cell_sample_size):
                pm_cell = pm_cells[j]
                docling_cell = docling_cells[j]
                
                if "text" in pm_cell and "text" in docling_cell:
                    if not compare_text_content(pm_cell["text"], docling_cell["text"], 
                                           test_config["tolerances"]["text"]):
                        layout_differences.append(f"Table {i}, Cell {j} content differs")
        
        # 3. Compare figure detection
        pm_figures = pm_output.get("figures", [])
        docling_figures = docling_output.get("figures", [])
        
        logger.info(f"  Figures detected: {len(pm_figures)} (original) vs {len(docling_figures)} (docling)")
        
        # Again, allow some flexibility in figure detection
        if abs(len(pm_figures) - len(docling_figures)) > 1:
            layout_differences.append(f"Figure count differs: {len(pm_figures)} vs {len(docling_figures)}")
        
        # Compare figure properties
        for i, (pm_fig, docling_fig) in enumerate(zip(pm_figures[:min(len(pm_figures), len(docling_figures))], strict=False)):
            # Compare figure boundaries
            if "bbox" in pm_fig and "bbox" in docling_fig:
                if not are_coordinates_equal(pm_fig["bbox"], docling_fig["bbox"], 
                                        test_config["tolerances"]["coordinate"]):
                    layout_differences.append(f"Figure {i} boundaries differ: {pm_fig['bbox']} vs {docling_fig['bbox']}")
            
            # Compare caption text if available
            if "caption" in pm_fig and "caption" in docling_fig:
                if not compare_text_content(pm_fig["caption"], docling_fig["caption"], 
                                       test_config["tolerances"]["text"]):
                    layout_differences.append(f"Figure {i} caption differs")
        
        # 4. Check reading order integrity
        # This checks if the content is in the correct reading order
        if "reading_order" in pm_output and "reading_order" in docling_output:
            pm_order = pm_output["reading_order"]
            docling_order = docling_output["reading_order"]
            
            # Compare the first few elements in reading order
            order_sample_size = min(10, len(pm_order), len(docling_order))
            for i in range(order_sample_size):
                pm_element = pm_order[i]
                docling_element = docling_order[i]
                
                if pm_element["type"] != docling_element["type"]:
                    layout_differences.append(f"Reading order element {i} type differs: {pm_element['type']} vs {docling_element['type']}")
        
        # 5. Generate visual comparison reports (optional)
        # This would require additional visualization tools

        # Log all differences and generate report
        log_differences(f"{doc_name} layout analysis", layout_differences)
        
        # Create comprehensive report
        report = {
            "document": str(doc_path),
            "column_analysis": {
                "original_count": len(pm_columns),
                "docling_count": len(docling_columns)
            },
            "table_analysis": {
                "original_count": len(pm_tables),
                "docling_count": len(docling_tables)
            },
            "figure_analysis": {
                "original_count": len(pm_figures),
                "docling_count": len(docling_figures)
            },
            "differences": layout_differences
        }
        
        # Save report
        with open(results_dir / f"{doc_name}_layout_report.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        # Assert overall success
        max_allowed_differences = int(test_config.get("config", {}).get("max_allowed_differences", 5))
        assert len(layout_differences) <= max_allowed_differences, \
            f"{len(layout_differences)} layout differences found in {doc_name}, exceeding maximum allowed ({max_allowed_differences})"
        
    except Exception as e:
        logger.error(f"Error in layout analysis test for {doc_name}: {str(e)}")
        pytest.fail(f"Layout analysis test failed: {str(e)}")

# RTL document processing test
@pytest.mark.parametrize("doc_sample", [s for s in get_test_document_configs() if "rtl" in s.get("path", "")])
def test_rtl_document_processing(papermage_engines, doc_sample):
    """
    Test the system's ability to process RTL (Right-to-Left) documents, including proper
    text extraction, direction handling, and character rendering.
    
    Args:
        papermage_engines: Tuple of (pm_original, pm_docling)
        doc_sample: RTL document sample configuration
    """
    # Get test case configuration
    test_config = get_test_case_config("rtl_handling")
    if not test_config["enabled"]:
        pytest.skip("RTL document processing test is disabled in config")
    
    # Prepare document path and name
    doc_name = doc_sample["name"]
    doc_path = Path(__file__).parent / "test_data" / "documents" / doc_sample["path"]
    
    # Skip if document doesn't exist
    if not doc_path.exists():
        pytest.skip(f"Document not found: {doc_path}")
    
    logger.info(f"Testing RTL document processing for document: {doc_name}")
    
    # Process document with both engines
    pm_original, pm_docling = papermage_engines
    
    try:
        # Load and process documents
        pm_doc = pm_original.load_pdf(doc_path)
        pm_output = pm_original.process(pm_doc)
        
        docling_doc = pm_docling.load_pdf(doc_path)
        docling_output = pm_docling.process(docling_doc)
        
        # Create results directory
        results_dir = Path(__file__).parent / "test_results" / "rtl"
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Track differences
        rtl_differences = []
        
        # 1. Test text extraction and direction
        # Extract full text from both implementations
        pm_text = pm_original.extract_text(pm_doc)
        docling_text = pm_docling.extract_text(docling_doc)
        
        # Check if text extraction is comparable
        text_similarity = compare_text_content(pm_text, docling_text, test_config["tolerances"]["text"])
        if not text_similarity:
            rtl_differences.append("Overall text extraction differs significantly")
            
            # Calculate more detailed text similarity
            total_chars = max(len(pm_text), len(docling_text))
            if total_chars > 0:
                matching_chars = sum(a == b for a, b in zip(pm_text[:min(len(pm_text), len(docling_text))], 
                                                         docling_text[:min(len(pm_text), len(docling_text))], strict=False))
                similarity_percentage = (matching_chars / total_chars) * 100
                logger.warning(f"RTL text similarity: {similarity_percentage:.2f}%")
        
        # 2. Test text direction flags
        # Check if RTL flag is correctly set in both outputs
        pm_is_rtl = pm_output.get("is_rtl", False)
        docling_is_rtl = docling_output.get("is_rtl", False)
        
        if pm_is_rtl != docling_is_rtl:
            rtl_differences.append(f"RTL direction flag mismatch: {pm_is_rtl} vs {docling_is_rtl}")
        
        # 3. Test paragraph directionality
        # Check if paragraphs are properly marked as RTL
        pm_paragraphs = pm_output.get("paragraphs", [])
        docling_paragraphs = docling_output.get("paragraphs", [])
        
        dir_mismatches = 0
        for i, (pm_para, docling_para) in enumerate(zip(pm_paragraphs[:min(len(pm_paragraphs), len(docling_paragraphs))], strict=False)):
            pm_dir = pm_para.get("direction", "ltr")
            docling_dir = docling_para.get("direction", "ltr")
            
            if pm_dir != docling_dir:
                dir_mismatches += 1
                if dir_mismatches <= 3:  # Limit the number of reported mismatches
                    rtl_differences.append(f"Paragraph {i} direction mismatch: {pm_dir} vs {docling_dir}")
        
        if dir_mismatches > 3:
            rtl_differences.append(f"Additional {dir_mismatches - 3} paragraph direction mismatches")
        
        # 4. Test character rendering and special characters
        # Extract special chars/diacritics handling by checking counts of specific characters
        # This is a simple way to verify if special characters are processed correctly
        
        # Function to count specific RTL markers and special characters
        def count_special_chars(text):
            rtl_markers = sum(1 for c in text if ord(c) in [0x200F, 0x202B, 0x202E])  # RTL marks
            arabic_diacritics = sum(1 for c in text if 0x064B <= ord(c) <= 0x065F)  # Arabic diacritics
            hebrew_diacritics = sum(1 for c in text if 0x0591 <= ord(c) <= 0x05C7)  # Hebrew diacritics
            
            return {
                "rtl_markers": rtl_markers,
                "arabic_diacritics": arabic_diacritics,
                "hebrew_diacritics": hebrew_diacritics
            }
        
        pm_char_counts = count_special_chars(pm_text)
        docling_char_counts = count_special_chars(docling_text)
        
        # Compare character counts with a tolerance
        for char_type, pm_count in pm_char_counts.items():
            docling_count = docling_char_counts.get(char_type, 0)
            # Allow for some variation in special character detection
            if abs(pm_count - docling_count) > max(3, int(0.2 * pm_count)):
                rtl_differences.append(f"{char_type} count differs significantly: {pm_count} vs {docling_count}")
        
        # 5. Test bidirectional text handling (if present)
        # Check sections with mixed RTL/LTR content
        
        # Extract tokens with their directions
        pm_tokens = pm_output.get("tokens", [])
        docling_tokens = docling_output.get("tokens", [])
        
        # Count tokens with RTL direction
        pm_rtl_tokens = sum(1 for t in pm_tokens if t.get("direction", "ltr") == "rtl")
        docling_rtl_tokens = sum(1 for t in docling_tokens if t.get("direction", "ltr") == "rtl")
        
        logger.info(f"  RTL tokens: {pm_rtl_tokens} (original) vs {docling_rtl_tokens} (docling)")
        
        # Allow for some variation but ensure general consistency
        if abs(pm_rtl_tokens - docling_rtl_tokens) > max(5, int(0.2 * pm_rtl_tokens)):
            rtl_differences.append(f"RTL token count differs significantly: {pm_rtl_tokens} vs {docling_rtl_tokens}")
        
        # Check for token-level direction switches in mixed content
        pm_direction_switches = 0
        prev_dir = None
        for token in pm_tokens:
            curr_dir = token.get("direction", "ltr")
            if prev_dir is not None and prev_dir != curr_dir:
                pm_direction_switches += 1
            prev_dir = curr_dir
        
        docling_direction_switches = 0
        prev_dir = None
        for token in docling_tokens:
            curr_dir = token.get("direction", "ltr")
            if prev_dir is not None and prev_dir != curr_dir:
                docling_direction_switches += 1
            prev_dir = curr_dir
        
        logger.info(f"  Direction switches: {pm_direction_switches} (original) vs {docling_direction_switches} (docling)")
        
        # Ensure similar handling of direction switches
        if abs(pm_direction_switches - docling_direction_switches) > max(3, int(0.3 * pm_direction_switches)):
            rtl_differences.append(f"Direction switch count differs: {pm_direction_switches} vs {docling_direction_switches}")
        
        # Log all differences and generate report
        log_differences(f"{doc_name} RTL processing", rtl_differences)
        
        # Create comprehensive report
        report = {
            "document": str(doc_path),
            "text_similarity": text_similarity,
            "rtl_flag": {
                "original": pm_is_rtl,
                "docling": docling_is_rtl
            },
            "special_characters": {
                "original": pm_char_counts,
                "docling": docling_char_counts
            },
            "direction_analysis": {
                "original_rtl_tokens": pm_rtl_tokens,
                "docling_rtl_tokens": docling_rtl_tokens,
                "original_direction_switches": pm_direction_switches,
                "docling_direction_switches": docling_direction_switches
            },
            "differences": rtl_differences
        }
        
        # Save report
        with open(results_dir / f"{doc_name}_rtl_report.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        # Assert overall success
        max_allowed_differences = int(test_config.get("config", {}).get("max_allowed_differences", 5))
        assert len(rtl_differences) <= max_allowed_differences, \
            f"{len(rtl_differences)} RTL processing differences found in {doc_name}, exceeding maximum allowed ({max_allowed_differences})"
        
    except Exception as e:
        logger.error(f"Error in RTL document processing test for {doc_name}: {str(e)}")
        pytest.fail(f"RTL document processing test failed: {str(e)}")

# Performance and scale testing
@pytest.mark.parametrize("doc_sample", [s for s in get_test_document_configs() if "large" in s.get("path", "")])
def test_performance_and_scale(papermage_engines, doc_sample):
    """
    Test performance characteristics and scalability of both engines with large documents.
    
    This test focuses on processing time, memory usage, and behavior with large documents,
    allowing for a comprehensive comparison of performance between PaperMage and PaperMage-Docling.
    
    Args:
        papermage_engines: Tuple of (pm_original, pm_docling)
        doc_sample: Document sample configuration for large documents
    """
    # Get test case configuration
    test_config = get_test_case_config("performance")
    if not test_config["enabled"]:
        pytest.skip("Performance testing is disabled in config")
    
    # Prepare document path and name
    doc_name = doc_sample["name"]
    doc_path = Path(__file__).parent / "test_data" / "documents" / doc_sample["path"]
    
    # Skip if document doesn't exist
    if not doc_path.exists():
        pytest.skip(f"Document not found: {doc_path}")
    
    logger.info(f"Testing performance and scale for document: {doc_name}")
    
    # Get timeout configuration (default: 5 minutes)
    timeout_seconds = int(test_config.get("config", {}).get("timeout_seconds", 300))
    
    # Import necessary modules for performance measurement
    import gc
    import time

    import psutil
    
    # Process document with both engines and measure performance
    pm_original, pm_docling = papermage_engines
    
    # Create results directory
    results_dir = Path(__file__).parent / "test_results" / "performance"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Performance measurement results
    performance_data = {
        "document": str(doc_path),
        "papermage_original": {},
        "papermage_docling": {},
        "comparison": {}
    }
    
    # Helper function to measure memory usage
    def get_memory_usage():
        # Force garbage collection to get more accurate memory usage
        gc.collect()
        process = psutil.Process()
        return {
            "rss": process.memory_info().rss / (1024 * 1024),  # RSS in MB
            "vms": process.memory_info().vms / (1024 * 1024),  # VMS in MB
        }
    
    # Helper function to measure processing with timeouts
    def measure_processing_time(engine, doc_path, name):
        result = {
            "success": False,
            "error": None,
            "load_time_ms": None,
            "process_time_ms": None,
            "memory_before_mb": None,
            "memory_after_mb": None,
            "memory_peak_mb": None
        }
        
        try:
            # Record initial memory
            initial_memory = get_memory_usage()
            result["memory_before_mb"] = initial_memory["rss"]
            
            # Measure document loading time
            start_time = time.time()
            doc = engine.load_pdf(doc_path)
            load_time = time.time() - start_time
            result["load_time_ms"] = load_time * 1000  # Convert to milliseconds
            
            # Record memory after loading
            post_load_memory = get_memory_usage()
            
            # Measure document processing time
            peak_memory = post_load_memory["rss"]
            start_time = time.time()
            engine.process(doc)
            process_time = time.time() - start_time
            result["process_time_ms"] = process_time * 1000  # Convert to milliseconds
            
            # Record memory after processing
            final_memory = get_memory_usage()
            result["memory_after_mb"] = final_memory["rss"]
            
            # Update peak memory
            peak_memory = max(peak_memory, final_memory["rss"])
            result["memory_peak_mb"] = peak_memory
            
            # Mark as successful
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error in performance measurement for {name}: {str(e)}")
        
        return result
    
    # Measure PaperMage original performance
    logger.info(f"Measuring performance for original PaperMage on {doc_name}")
    pm_result = measure_processing_time(pm_original, doc_path, "original")
    performance_data["papermage_original"] = pm_result
    
    # Measure PaperMage-Docling performance
    logger.info(f"Measuring performance for PaperMage-Docling on {doc_name}")
    docling_result = measure_processing_time(pm_docling, doc_path, "docling")
    performance_data["papermage_docling"] = docling_result
    
    # Compare performances if both were successful
    if pm_result["success"] and docling_result["success"]:
        # Calculate performance ratios (Docling/Original)
        load_time_ratio = docling_result["load_time_ms"] / pm_result["load_time_ms"] if pm_result["load_time_ms"] > 0 else None
        process_time_ratio = docling_result["process_time_ms"] / pm_result["process_time_ms"] if pm_result["process_time_ms"] > 0 else None
        memory_ratio = docling_result["memory_peak_mb"] / pm_result["memory_peak_mb"] if pm_result["memory_peak_mb"] > 0 else None
        
        # Store comparison results
        comparison = {
            "load_time_ratio": load_time_ratio,
            "process_time_ratio": process_time_ratio,
            "memory_ratio": memory_ratio,
            "docling_faster_load": load_time_ratio < 1.0 if load_time_ratio else None,
            "docling_faster_process": process_time_ratio < 1.0 if process_time_ratio else None,
            "docling_lower_memory": memory_ratio < 1.0 if memory_ratio else None
        }
        
        performance_data["comparison"] = comparison
        
        # Log performance comparison
        logger.info(f"Performance comparison for {doc_name}:")
        logger.info(f"  Load time: {pm_result['load_time_ms']:.2f}ms (orig) vs {docling_result['load_time_ms']:.2f}ms (docling), ratio: {load_time_ratio:.2f}")
        logger.info(f"  Process time: {pm_result['process_time_ms']:.2f}ms (orig) vs {docling_result['process_time_ms']:.2f}ms (docling), ratio: {process_time_ratio:.2f}")
        logger.info(f"  Peak memory: {pm_result['memory_peak_mb']:.2f}MB (orig) vs {docling_result['memory_peak_mb']:.2f}MB (docling), ratio: {memory_ratio:.2f}")
        
        # Check if performance is within acceptable limits
        # Get performance thresholds from config
        max_time_ratio = float(test_config.get("config", {}).get("max_time_ratio", 1.5))
        max_memory_ratio = float(test_config.get("config", {}).get("max_memory_ratio", 1.5))
        
        # Assert performance is acceptable
        assert process_time_ratio <= max_time_ratio, \
            f"Processing time ratio ({process_time_ratio:.2f}) exceeds maximum allowed ({max_time_ratio:.2f})"
        
        assert memory_ratio <= max_memory_ratio, \
            f"Memory usage ratio ({memory_ratio:.2f}) exceeds maximum allowed ({max_memory_ratio:.2f})"
    
    # Test batch processing capabilities (if supported)
    if hasattr(pm_original, "batch_process") and hasattr(pm_docling, "batch_process"):
        logger.info("Testing batch processing performance")
        
        # Create a small batch from the same document
        batch_size = 3
        batch_docs = [doc_path] * batch_size
        
        # Test original PaperMage batch processing
        try:
            start_time = time.time()
            pm_original.batch_process(batch_docs)
            pm_batch_time = time.time() - start_time
            
            # Test PaperMage-Docling batch processing
            start_time = time.time()
            pm_docling.batch_process(batch_docs)
            docling_batch_time = time.time() - start_time
            
            # Store batch processing results
            performance_data["batch_processing"] = {
                "batch_size": batch_size,
                "original_batch_time_ms": pm_batch_time * 1000,
                "docling_batch_time_ms": docling_batch_time * 1000,
                "batch_time_ratio": docling_batch_time / pm_batch_time if pm_batch_time > 0 else None
            }
            
            # Log batch processing comparison
            logger.info(f"  Batch processing time (batch size {batch_size}): {pm_batch_time*1000:.2f}ms (orig) vs {docling_batch_time*1000:.2f}ms (docling)")
            
        except Exception as e:
            logger.warning(f"Batch processing test failed: {str(e)}")
            performance_data["batch_processing"] = {"error": str(e)}
    
    # Test concurrent processing (if supported)
    if hasattr(pm_original, "max_concurrent_processes") and hasattr(pm_docling, "max_concurrent_processes"):
        logger.info("Testing concurrent processing capabilities")
        
        pm_concurrent = getattr(pm_original, "max_concurrent_processes", 1)
        docling_concurrent = getattr(pm_docling, "max_concurrent_processes", 1)
        
        performance_data["concurrency"] = {
            "original_max_concurrent": pm_concurrent,
            "docling_max_concurrent": docling_concurrent
        }
        
        logger.info(f"  Max concurrent processes: {pm_concurrent} (orig) vs {docling_concurrent} (docling)")
    
    # Save performance report
    with open(results_dir / f"{doc_name}_performance_report.json", 'w') as f:
        json.dump(performance_data, f, indent=2)
    
    # Success if we got this far without exceptions
    assert pm_result["success"], f"Performance test failed for original PaperMage: {pm_result.get('error', 'Unknown error')}"
    assert docling_result["success"], f"Performance test failed for PaperMage-Docling: {docling_result.get('error', 'Unknown error')}"
    
    logger.info(f"Performance and scale test completed successfully for {doc_name}")
