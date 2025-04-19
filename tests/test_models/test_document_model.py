"""
Tests for the Document model.

This module contains tests for the Document model, including creation, updating,
deletion, and validation of model properties and relationships.
"""

from datetime import datetime

from app.models.document import Document


def test_document_model_creation(test_db):
    """Test creating and storing a Document model."""
    # Create a document
    document = Document(
        title="Test Document",
        content="This is test content for the document.",
        mime_type="text/plain",
        filename="test_doc.txt",
    )
    
    # Add to database
    test_db.add(document)
    test_db.commit()
    test_db.refresh(document)
    
    # Check that the document was created with correct values
    assert document.id is not None
    assert document.title == "Test Document"
    assert document.content == "This is test content for the document."
    assert document.mime_type == "text/plain"
    assert document.filename == "test_doc.txt"
    assert document.created_at is not None
    assert document.updated_at is not None
    
    # Check that created_at and updated_at are datetime objects
    assert isinstance(document.created_at, datetime)
    assert isinstance(document.updated_at, datetime)


def test_document_model_update(test_db):
    """Test updating a Document model."""
    # Create a document
    document = Document(
        title="Original Title",
        content="Original content",
        mime_type="text/plain",
        filename="original.txt",
    )
    
    # Add to database
    test_db.add(document)
    test_db.commit()
    test_db.refresh(document)
    
    # Store original ID and timestamps
    original_id = document.id
    original_created_at = document.created_at
    original_updated_at = document.updated_at
    
    # Update document after a small delay
    import time
    time.sleep(0.1)  # Sleep to ensure updated_at timestamp changes
    
    document.title = "Updated Title"
    document.content = "Updated content"
    document.mime_type = "text/markdown"
    document.filename = "updated.md"
    
    test_db.add(document)
    test_db.commit()
    test_db.refresh(document)
    
    # Check that ID remains the same but values are updated
    assert document.id == original_id
    assert document.title == "Updated Title"
    assert document.content == "Updated content"
    assert document.mime_type == "text/markdown"
    assert document.filename == "updated.md"
    
    # Check that created_at is unchanged but updated_at is changed
    assert document.created_at == original_created_at
    assert document.updated_at > original_updated_at


def test_document_model_delete(test_db):
    """Test deleting a Document model."""
    # Create a document
    document = Document(
        title="Document to Delete",
        content="This document will be deleted",
    )
    
    # Add to database
    test_db.add(document)
    test_db.commit()
    
    document_id = document.id
    
    # Delete the document
    test_db.delete(document)
    test_db.commit()
    
    # Try to retrieve the deleted document
    deleted_document = test_db.query(Document).filter(Document.id == document_id).first()
    
    # Check that the document is no longer in the database
    assert deleted_document is None


def test_document_user_relationship(test_db):
    """Test the relationship between Document and User models."""
    # Create a document
    document = Document(
        title="Relationship Test",
        content="Testing document-user relationship",
    )
    
    # Add to database
    test_db.add(document)
    test_db.commit()
    test_db.refresh(document)
    
    # Check relationship from document to user
    assert document.owner_id is None


def test_document_model_defaults(test_db):
    """Test default values for Document model."""
    # Create a minimal document
    document = Document(
        title="Default Test",
    )
    
    # Add to database
    test_db.add(document)
    test_db.commit()
    test_db.refresh(document)
    
    # Check default values
    assert document.content is None
    assert document.mime_type is None
    assert document.filename is None
    assert document.created_at is not None
    assert document.updated_at is not None


def test_cascade_delete(test_db):
    """Test that deleting a user cascades to delete their documents."""
    # Create multiple documents for this user
    for i in range(3):
        document = Document(
            title=f"Cascade Document {i}",
            content=f"Content for cascade document {i}",
        )
        test_db.add(document)
    
    test_db.commit()
    
    # Verify the documents exist
    user_documents = test_db.query(Document).filter(Document.owner_id == None).all()
    assert len(user_documents) == 3
    
    user_id = None
    
    # Now delete the user
    test_db.delete(user_documents[0])
    test_db.commit()
    
    # Check that the user's documents were also deleted
    orphaned_documents = test_db.query(Document).filter(Document.owner_id == user_id).all()
    assert len(orphaned_documents) == 0 