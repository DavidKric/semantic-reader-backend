"""
Tests for the document API endpoints.

This module contains tests for the document API endpoints in app.api.v1.documents,
particularly testing database integration and external API fallback.
"""

import pytest
import io
from unittest.mock import patch, MagicMock
import json

from app.models.document import Document, Page, Section, Paragraph
from app.services.document_processing_service import DocumentProcessingService


@patch.object(DocumentProcessingService, 'external_api_available', True)
@patch.object(DocumentProcessingService, 'api_service')
def test_parse_document_endpoint(mock_api_service, client, test_db):
    """Test the parse document endpoint."""
    # Mock API service response
    mock_api_service.process_document.return_value = {
        "id": "test-id",
        "metadata": {
            "language": "en",
            "is_rtl_language": False
        },
        "pages": [{"page_number": 1}],
        "words": ["word1", "word2"]
    }
    
    # Create test file
    file_content = b"test file content"
    
    # Send request
    response = client.post(
        "/api/v1/parse",
        files={"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.pdf"
    assert data["processing_status"] == "completed"
    assert data["is_processed"] is True
    
    # Verify database
    documents = test_db.query(Document).all()
    assert len(documents) == 1
    assert documents[0].filename == "test.pdf"
    assert documents[0].file_type == "pdf"
    assert documents[0].processing_status == "completed"


@patch.object(DocumentProcessingService, 'external_api_available', True)
def test_health_endpoint(client):
    """Test the health endpoint reports correct status."""
    # Send request
    response = client.get("/api/v1/health")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "database" in data
    assert "external_api" in data
    assert data["external_api"] == "available"


@patch.object(DocumentProcessingService, 'external_api_available', True)
def test_get_document_endpoint(client, sample_document):
    """Test the get document endpoint."""
    # Send request
    response = client.get(f"/api/v1/documents/{sample_document.id}")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_document.id
    assert data["title"] == sample_document.title
    assert data["filename"] == sample_document.filename


@patch.object(DocumentProcessingService, 'external_api_available', True)
@patch.object(DocumentProcessingService, 'api_service')
def test_get_document_as_papermage(mock_api_service, client, sample_document):
    """Test getting a document in PaperMage format."""
    # Update sample document with storage ID
    sample_document.storage_id = "sample-storage-id"
    client.app.dependency_overrides.get("get_db")().commit()
    
    # Mock API service response
    mock_api_service.get_document.return_value = {
        "id": "sample-storage-id",
        "papermage": True,
        "content": "PaperMage content"
    }
    
    # Send request
    response = client.get(f"/api/v1/documents/{sample_document.id}?as_papermage=true")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "papermage" in data
    assert data["papermage"] is True


@patch.object(DocumentProcessingService, 'external_api_available', True)
def test_list_documents_endpoint(client, sample_document):
    """Test the list documents endpoint."""
    # Send request
    response = client.get("/api/v1/documents")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    
    # Verify sample document is in response
    found = False
    for item in data["items"]:
        if item["id"] == sample_document.id:
            found = True
            assert item["title"] == sample_document.title
            assert item["filename"] == sample_document.filename
            break
    
    assert found, "Sample document not found in response"


@patch.object(DocumentProcessingService, 'external_api_available', True)
def test_list_documents_with_params(client, sample_document):
    """Test the list documents endpoint with parameters."""
    # Send request with parameters
    response = client.get(
        "/api/v1/documents?page=1&page_size=5&include_external=false&sync_with_external=false"
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["page"] == 1
    assert data["page_size"] == 5


@patch.object(DocumentProcessingService, 'external_api_available', True)
@patch.object(DocumentProcessingService, 'api_service')
def test_delete_document_endpoint(mock_api_service, client, sample_document):
    """Test the delete document endpoint."""
    # Mock API service delete response
    mock_api_service.delete_document.return_value = True
    
    # Send request
    response = client.delete(f"/api/v1/documents/{sample_document.id}")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Verify document is deleted from database
    document = client.get(f"/api/v1/documents/{sample_document.id}")
    assert document.status_code == 404


@patch.object(DocumentProcessingService, 'external_api_available', True)
def test_update_document_metadata_endpoint(client, sample_document):
    """Test updating document metadata."""
    # Prepare metadata
    metadata = {
        "custom_key": "custom_value",
        "tags": ["test", "document"]
    }
    
    # Send request
    response = client.patch(
        f"/api/v1/documents/{sample_document.id}/metadata",
        json=metadata
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_document.id
    assert "doc_metadata" in data
    assert data["doc_metadata"]["custom_key"] == "custom_value"
    assert "tags" in data["doc_metadata"]


@patch.object(DocumentProcessingService, 'external_api_available', True)
@patch.object(DocumentProcessingService, 'get_pipeline_stats')
def test_get_pipeline_stats_endpoint(mock_get_stats, client):
    """Test getting pipeline statistics."""
    # Mock stats response
    mock_get_stats.return_value = {
        "status": "ok",
        "documents_processed": 42,
        "average_processing_time": 1.5
    }
    
    # Send request
    response = client.get("/api/v1/stats/pipeline")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["documents_processed"] == 42


@patch.object(DocumentProcessingService, 'external_api_available', True)
@patch.object(DocumentProcessingService, 'get_cache_stats')
def test_get_cache_stats_endpoint(mock_get_stats, client):
    """Test getting cache statistics."""
    # Mock stats response
    mock_get_stats.return_value = {
        "status": "ok",
        "cache_size": 1024,
        "hit_rate": 0.8
    }
    
    # Send request
    response = client.get("/api/v1/stats/cache")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["cache_size"] == 1024


@patch.object(DocumentProcessingService, 'external_api_available', True)
@patch.object(DocumentProcessingService, 'clear_document_cache')
def test_clear_cache_endpoint(mock_clear_cache, client):
    """Test clearing the document cache."""
    # Mock clear cache response
    mock_clear_cache.return_value = True
    
    # Send request
    response = client.post("/api/v1/cache/clear")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True 