"""
Tests for the Document model.

This module contains tests for the Document model, including creation, updating,
deletion, and validation of model properties and relationships.
"""

import pytest
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.models.document import Document
from app.models.user import User


def test_document_model_creation(test_db):
    """Test creating and storing a Document model."""
    # Create a user first (document owner)
    user = User(
        username="docowner",
        email="owner@example.com",
        hashed_password="hashed_password_value"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Create a document
    document = Document(
        title="Test Document",
        content="This is test content for the document.",
        mime_type="text/plain",
        filename="test_doc.txt",
        owner_id=user.id
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
    assert document.owner_id == user.id
    assert document.created_at is not None
    assert document.updated_at is not None
    
    # Check that created_at and updated_at are datetime objects
    assert isinstance(document.created_at, datetime)
    assert isinstance(document.updated_at, datetime)


def test_document_model_update(test_db):
    """Test updating a Document model."""
    # Create a user first (document owner)
    user = User(
        username="docowner",
        email="owner@example.com",
        hashed_password="hashed_password_value"
    )
    test_db.add(user)
    test_db.commit()
    
    # Create a document
    document = Document(
        title="Original Title",
        content="Original content",
        mime_type="text/plain",
        filename="original.txt",
        owner_id=user.id
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
    # Create a user first (document owner)
    user = User(
        username="docowner",
        email="owner@example.com",
        hashed_password="hashed_password_value"
    )
    test_db.add(user)
    test_db.commit()
    
    # Create a document
    document = Document(
        title="Document to Delete",
        content="This document will be deleted",
        owner_id=user.id
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
    # Create a user first (document owner)
    user = User(
        username="relationuser",
        email="relation@example.com",
        hashed_password="hashed_password_value"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Create a document
    document = Document(
        title="Relationship Test",
        content="Testing document-user relationship",
        owner_id=user.id
    )
    
    # Add to database
    test_db.add(document)
    test_db.commit()
    test_db.refresh(document)
    
    # Check relationship from document to user
    assert document.owner_id == user.id
    assert document.owner.username == "relationuser"
    assert document.owner.email == "relation@example.com"
    
    # Check relationship from user to documents
    user_documents = test_db.query(Document).filter(Document.owner_id == user.id).all()
    assert len(user_documents) == 1
    assert user_documents[0].id == document.id
    assert user_documents[0].title == "Relationship Test"


def test_document_model_defaults(test_db):
    """Test default values for Document model."""
    # Create a user first (document owner)
    user = User(
        username="defaultuser",
        email="default@example.com",
        hashed_password="hashed_password_value"
    )
    test_db.add(user)
    test_db.commit()
    
    # Create a minimal document
    document = Document(
        title="Default Test",
        owner_id=user.id
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
    # Create a user
    user = User(
        username="cascadeuser",
        email="cascade@example.com",
        hashed_password="hashed_password_value"
    )
    test_db.add(user)
    test_db.commit()
    
    # Create multiple documents for this user
    for i in range(3):
        document = Document(
            title=f"Cascade Document {i}",
            content=f"Content for cascade document {i}",
            owner_id=user.id
        )
        test_db.add(document)
    
    test_db.commit()
    
    # Verify the documents exist
    user_documents = test_db.query(Document).filter(Document.owner_id == user.id).all()
    assert len(user_documents) == 3
    
    user_id = user.id
    
    # Now delete the user
    test_db.delete(user)
    test_db.commit()
    
    # Check that the user's documents were also deleted
    orphaned_documents = test_db.query(Document).filter(Document.owner_id == user_id).all()
    assert len(orphaned_documents) == 0 