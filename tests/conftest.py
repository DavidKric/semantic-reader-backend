"""
Pytest configuration file for PaperMage-Docling tests.

This file configures pytest for testing, including HTML report generation,
custom markers, and global test fixtures.
"""

import os
import json
import pytest
import logging
from pathlib import Path
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from pytest_html import extras

from app.main import app
from app.core.database import Base, get_db
from app.services.document_processing_service import DocumentProcessingService
from app.models.document import Document

# Get the test configuration file
CONFIG_FILE = Path(__file__).parent / "e2e_test_config.json"

# Define test directories for easy access
TEST_DIR = Path(__file__).parent
TEST_DATA_DIR = TEST_DIR / "data"
TEST_EXPECTED_DIR = TEST_DATA_DIR / "expected"
TEST_VISUALS_DIR = TEST_DIR / "visuals"

# Ensure visuals directory exists
TEST_VISUALS_DIR.mkdir(exist_ok=True)

def pytest_configure(config):
    """
    Configure pytest with custom markers and settings.
    """
    # Register custom markers
    config.addinivalue_line("markers", "simple: mark a test as using simple documents")
    config.addinivalue_line("markers", "complex: mark a test as using complex documents")
    config.addinivalue_line("markers", "rtl: mark a test as using RTL documents")
    config.addinivalue_line("markers", "large: mark a test as using large documents")
    config.addinivalue_line("markers", "performance: mark a test as a performance test")
    
    # Load test configuration
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            test_config = json.load(f)
            
        # Setup HTML reporting if enabled
        if test_config.get("html_report", {}).get("enabled", False):
            html_output_dir = Path(test_config["html_report"].get("output_dir", "test_results/html"))
            
            # Ensure the output directory exists
            os.makedirs(html_output_dir, exist_ok=True)
            
            # Generate timestamped report name
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_path = html_output_dir / f"e2e_test_report_{timestamp}.html"
            
            # Add HTML reporting options to pytest configuration
            if hasattr(config, 'option'):
                config.option.htmlpath = str(report_path)
                config.option.self_contained_html = True

def pytest_html_report_title(report):
    """
    Customize the HTML report title.
    """
    report.title = "PaperMage-Docling End-to-End Test Report"

def pytest_html_results_summary(prefix, summary, postfix):
    """
    Add custom summary information to the HTML report.
    """
    prefix.extend([
        "<p>End-to-end comparison tests between PaperMage-Docling and original PaperMage</p>",
        "<p>Test environment:</p>",
        "<ul>",
        f"<li>Python version: {pytest.__version__}</li>",
        f"<li>Test run date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>",
        "</ul>",
    ])

@pytest.fixture(scope="session")
def test_config():
    """
    Load and provide the test configuration from e2e_test_config.json.
    
    Returns:
        dict: The test configuration
    """
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        # Return default configuration if file doesn't exist
        return {
            "tolerances": {
                "coordinate": 2.0,
                "text": 0.95,
                "confidence": 0.05
            },
            "test_data_paths": {
                "simple": "test_data/documents/simple",
                "complex": "test_data/documents/complex",
                "rtl": "test_data/documents/rtl",
                "large": "test_data/documents/large"
            },
            "html_report": {
                "enabled": True,
                "output_dir": "test_results/html"
            }
        }

@pytest.fixture(scope="session")
def setup_test_environment():
    """
    Set up the test environment, including setting environment variables
    and initializing necessary resources.
    
    Returns:
        dict: Test environment information
    """
    # Store original environment variables
    original_env = {}
    for key in ['PAPERMAGE_CACHE_DIR', 'PAPERMAGE_DOCLING_CACHE_DIR']:
        original_env[key] = os.environ.get(key)
    
    # Set up testing environment variables
    os.environ['PAPERMAGE_CACHE_DIR'] = str(Path(__file__).parent / "test_data" / "cache" / "papermage")
    os.environ['PAPERMAGE_DOCLING_CACHE_DIR'] = str(Path(__file__).parent / "test_data" / "cache" / "papermage_docling")
    
    # Create cache directories
    Path(os.environ['PAPERMAGE_CACHE_DIR']).mkdir(parents=True, exist_ok=True)
    Path(os.environ['PAPERMAGE_DOCLING_CACHE_DIR']).mkdir(parents=True, exist_ok=True)
    
    # Return test environment info
    yield {
        "cache_dir_papermage": os.environ['PAPERMAGE_CACHE_DIR'],
        "cache_dir_papermage_docling": os.environ['PAPERMAGE_DOCLING_CACHE_DIR'],
    }
    
    # Cleanup and restore environment variables
    for key, value in original_env.items():
        if value is None:
            if key in os.environ:
                del os.environ[key]
        else:
            os.environ[key] = value 

@pytest.fixture(scope="function")
def test_db_engine():
    """Create a SQLite in-memory database engine for testing."""
    # Use in-memory SQLite for tests
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Drop tables after tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_db_engine):
    """Create a database session for testing."""
    # Create session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    # Create db session
    db = TestingSessionLocal()
    
    yield db
    
    # Close session after tests
    db.close()


@pytest.fixture(scope="function")
def client(test_db):
    """Create a FastAPI test client with a test database."""
    # Override the dependency to use the test database
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    test_client = TestClient(app)
    
    yield test_client
    
    # Clean up after tests
    app.dependency_overrides = {}


@pytest.fixture
def document_service(test_db):
    """
    Create a document processing service instance with the test database.
    
    Args:
        test_db: The test database session fixture
        
    Returns:
        DocumentProcessingService: Service instance with test DB
    """
    return DocumentProcessingService(db=test_db)


@pytest.fixture
def sample_document(test_db):
    """
    Create a sample document in the test database.
    
    Args:
        test_db: The test database session fixture
        
    Returns:
        Document: A sample document for testing
    """
    document = Document(
        title="Test Document",
        filename="test_document.pdf",
        file_type="pdf",
        processing_status="completed",
        is_processed=True,
        language="en",
        has_rtl=False,
        num_pages=5,
        word_count=1000,
        doc_metadata={"test": "metadata"}
    )
    
    test_db.add(document)
    test_db.commit()
    test_db.refresh(document)
    
    return document 

@pytest.fixture
def sample_pdfs():
    """Returns a dictionary of sample PDF paths."""
    # This will be populated when we add the actual PDFs
    return {
        "simple": None,  # Will be TEST_DATA_DIR / "sample1_simple.pdf"
        "multicolumn": None,
        "scanned": None,
        "tables": None,
        "figures": None,
        "mixed": None,
        "corrupt": None,
    }

@pytest.fixture
def expected_outputs():
    """Returns a dictionary of expected JSON outputs."""
    expected = {}
    for json_file in TEST_EXPECTED_DIR.glob("*.json"):
        with open(json_file, "r") as f:
            expected[json_file.stem] = json.load(f)
    return expected

@pytest.fixture
def attach_visual(request):
    """Fixture to attach visualization images to the HTML report."""
    def _attach_visual(image_path, name=None):
        if not name:
            name = os.path.basename(image_path)
        # Create a thumbnail and larger version for the HTML report
        request.node.user_properties.append(
            ("extra", extras.image(str(image_path), name))
        )
    return _attach_visual

@pytest.fixture
def compare_json():
    """Fixture to compare JSON outputs with expected outputs."""
    def _compare(actual, expected, ignore_keys=None):
        """
        Compare two JSON objects, optionally ignoring specific keys.
        
        Args:
            actual: The actual JSON object
            expected: The expected JSON object
            ignore_keys: List of keys to ignore in the comparison
            
        Returns:
            True if the JSONs match, False otherwise
        """
        if ignore_keys is None:
            ignore_keys = []
            
        if isinstance(actual, dict) and isinstance(expected, dict):
            # Check if all keys in expected are in actual
            for key in expected:
                if key in ignore_keys:
                    continue
                if key not in actual:
                    print(f"Key '{key}' missing from actual JSON")
                    return False
                if not _compare(actual[key], expected[key], ignore_keys):
                    print(f"Values don't match for key '{key}'")
                    return False
            
            # Check if all keys in actual are in expected
            for key in actual:
                if key in ignore_keys:
                    continue
                if key not in expected:
                    print(f"Unexpected key '{key}' in actual JSON")
                    return False
            
            return True
        
        elif isinstance(actual, list) and isinstance(expected, list):
            if len(actual) != len(expected):
                print(f"List lengths don't match: {len(actual)} vs {len(expected)}")
                return False
            
            # For simple lists of primitives, sort and compare
            if all(not isinstance(x, (dict, list)) for x in actual + expected):
                return sorted(actual) == sorted(expected)
            
            # For lists of objects, compare each pair
            for a_item, e_item in zip(actual, expected):
                if not _compare(a_item, e_item, ignore_keys):
                    return False
            
            return True
        
        else:
            # Compare primitive values
            equal = actual == expected
            if not equal:
                print(f"Values don't match: {actual} vs {expected}")
            return equal
    
    return _compare 