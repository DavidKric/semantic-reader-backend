"""
Pytest configuration file for PaperMage-Docling tests.

This file configures pytest for testing, including HTML report generation,
custom markers, and global test fixtures.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

import pytest
from app.core.database import Base, get_db
from app.main import create_app
from app.models.document import Document
from app.services.document_processing_service import DocumentProcessingService
from fastapi.testclient import TestClient
from pytest_html import extras
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Get the test configuration file
CONFIG_FILE = Path(__file__).parent / "e2e_test_config.json"

# Define test directories for easy access
TEST_DIR = Path(__file__).parent
TEST_DATA_DIR = TEST_DIR / "data"
TEST_FIXTURES_DIR = TEST_DATA_DIR / "fixtures"  # New directory for test fixtures
TEST_SAMPLES_DIR = TEST_FIXTURES_DIR / "samples"  # Test sample files organized by type
TEST_EXPECTED_DIR = TEST_FIXTURES_DIR / "expected"  # Expected outputs
TEST_TEMP_DIR = TEST_DATA_DIR / "temp"  # Temporary files created during tests
TEST_CACHE_DIR = TEST_DATA_DIR / "cache"  # Cache directories
TEST_VISUALS_DIR = TEST_DIR / "visuals"

# Ensure directories exist
TEST_VISUALS_DIR.mkdir(exist_ok=True)
TEST_FIXTURES_DIR.mkdir(exist_ok=True)
TEST_SAMPLES_DIR.mkdir(exist_ok=True)
TEST_EXPECTED_DIR.mkdir(exist_ok=True)
TEST_TEMP_DIR.mkdir(exist_ok=True)

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

@pytest.fixture(scope="session", autouse=True)
def setup_test_data():
    """
    Set up the test data directory structure at the beginning of the test session.
    This fixture runs automatically due to autouse=True.
    """
    # Create sample types directories
    sample_types = ["simple", "complex", "rtl", "tables", "figures", "multi_column", "corrupt", "invalid"]
    for sample_type in sample_types:
        (TEST_SAMPLES_DIR / sample_type).mkdir(exist_ok=True)
    
    # Migrate existing sample files if needed
    old_data_dir = TEST_DATA_DIR / "data"
    if old_data_dir.exists():
        # Move sample PDFs to appropriate directories
        pdf_mapping = {
            "sample1_simple.pdf": "simple",
            "sample2_multicolumn.pdf": "multi_column",
            "sample3_scanned.pdf": "complex",
            "sample4_tables.pdf": "tables",
            "sample5_figures.pdf": "figures",
            "sample6_mixed.pdf": "complex",
            "corrupt.pdf": "corrupt"
        }
        
        for pdf_file, folder in pdf_mapping.items():
            source = old_data_dir / pdf_file
            if source.exists():
                dest = TEST_SAMPLES_DIR / folder / pdf_file
                if not dest.exists():
                    shutil.copy(str(source), str(dest))
        
        # Move expected outputs
        old_expected_dir = old_data_dir / "expected"
        if old_expected_dir.exists() and old_expected_dir.is_dir():
            for json_file in old_expected_dir.glob("*.json"):
                dest = TEST_EXPECTED_DIR / json_file.name
                if not dest.exists():
                    shutil.copy(str(json_file), str(dest))
    
    # Also check and copy from the old documents directory
    old_docs_dir = TEST_DATA_DIR / "documents"
    if old_docs_dir.exists():
        for category in ["simple", "complex", "rtl", "large"]:
            old_category_dir = old_docs_dir / category
            if old_category_dir.exists() and old_category_dir.is_dir():
                for pdf_file in old_category_dir.glob("*.pdf"):
                    dest = TEST_SAMPLES_DIR / category / pdf_file.name
                    if not dest.exists():
                        shutil.copy(str(pdf_file), str(dest))
    
    # Copy invalid text file
    invalid_text = TEST_DATA_DIR / "invalid.txt"
    if invalid_text.exists():
        dest = TEST_SAMPLES_DIR / "invalid" / "invalid.txt"
        if not dest.exists():
            shutil.copy(str(invalid_text), str(dest))
    
    yield  # Allow tests to run
    
    # Clean up temporary files after all tests complete
    for tmp_file in TEST_TEMP_DIR.glob("*"):
        try:
            if tmp_file.is_file():
                tmp_file.unlink()
            elif tmp_file.is_dir():
                shutil.rmtree(tmp_file)
        except Exception:
            pass  # Ignore errors during cleanup

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
                "simple": str(TEST_SAMPLES_DIR / "simple"),
                "complex": str(TEST_SAMPLES_DIR / "complex"),
                "rtl": str(TEST_SAMPLES_DIR / "rtl"),
                "large": str(TEST_SAMPLES_DIR / "large"),
                "tables": str(TEST_SAMPLES_DIR / "tables"),
                "figures": str(TEST_SAMPLES_DIR / "figures"),
                "multi_column": str(TEST_SAMPLES_DIR / "multi_column"),
                "corrupt": str(TEST_SAMPLES_DIR / "corrupt"),
                "invalid": str(TEST_SAMPLES_DIR / "invalid"),
                "expected": str(TEST_EXPECTED_DIR),
                "temp": str(TEST_TEMP_DIR)
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
    os.environ['PAPERMAGE_CACHE_DIR'] = str(TEST_CACHE_DIR / "papermage")
    os.environ['PAPERMAGE_DOCLING_CACHE_DIR'] = str(TEST_CACHE_DIR / "papermage_docling")
    
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


@pytest.fixture
def client():
    """Create a FastAPI test client with a dummy DB override."""
    app = create_app()

    def override_get_db():
        class DummySession:
            def close(self): pass
        yield DummySession()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client


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
    return {
        "simple": TEST_SAMPLES_DIR / "simple" / "sample1_simple.pdf",
        "multicolumn": TEST_SAMPLES_DIR / "multi_column" / "sample2_multicolumn.pdf",
        "scanned": TEST_SAMPLES_DIR / "complex" / "sample3_scanned.pdf",
        "tables": TEST_SAMPLES_DIR / "tables" / "sample4_tables.pdf",
        "figures": TEST_SAMPLES_DIR / "figures" / "sample5_figures.pdf",
        "mixed": TEST_SAMPLES_DIR / "complex" / "sample6_mixed.pdf",
        "corrupt": TEST_SAMPLES_DIR / "corrupt" / "corrupt.pdf",
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
def temp_dir():
    """Returns the temporary directory path for test file operations."""
    return TEST_TEMP_DIR

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
            for a_item, e_item in zip(actual, expected, strict=False):
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