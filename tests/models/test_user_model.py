"""
Tests for the User model.

This module contains tests for the User model, including creation, updating,
deletion, and validation of model properties and relationships.
"""

import pytest
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.models.user import User


def test_user_model_creation(test_db):
    """Test creating and storing a User model."""
    # Create a user
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed_password_value",
        is_active=True,
        is_superuser=False
    )
    
    # Add to database
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Check that the user was created with correct values
    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.full_name == "Test User"
    assert user.hashed_password == "hashed_password_value"
    assert user.is_active is True
    assert user.is_superuser is False
    assert user.created_at is not None
    assert user.updated_at is not None
    
    # Check that created_at and updated_at are datetime objects
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)


def test_user_model_update(test_db):
    """Test updating a User model."""
    # Create a user
    user = User(
        username="oldusername",
        email="old@example.com",
        full_name="Old Name",
        hashed_password="old_password",
        is_active=True
    )
    
    # Add to database
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Store original ID and timestamps
    original_id = user.id
    original_created_at = user.created_at
    original_updated_at = user.updated_at
    
    # Update user after a small delay
    import time
    time.sleep(0.1)  # Sleep to ensure updated_at timestamp changes
    
    user.username = "newusername"
    user.email = "new@example.com"
    user.full_name = "New Name"
    
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Check that ID remains the same but values are updated
    assert user.id == original_id
    assert user.username == "newusername"
    assert user.email == "new@example.com"
    assert user.full_name == "New Name"
    
    # Check that created_at is unchanged but updated_at is changed
    assert user.created_at == original_created_at
    assert user.updated_at > original_updated_at


def test_user_model_delete(test_db):
    """Test deleting a User model."""
    # Create a user
    user = User(
        username="deleteuser",
        email="delete@example.com",
        hashed_password="password"
    )
    
    # Add to database
    test_db.add(user)
    test_db.commit()
    
    user_id = user.id
    
    # Delete the user
    test_db.delete(user)
    test_db.commit()
    
    # Try to retrieve the deleted user
    deleted_user = test_db.query(User).filter(User.id == user_id).first()
    
    # Check that the user is no longer in the database
    assert deleted_user is None


def test_user_unique_constraints(test_db):
    """Test unique constraints on User model."""
    # Create a user
    user1 = User(
        username="uniqueuser",
        email="unique@example.com",
        hashed_password="password"
    )
    
    # Add to database
    test_db.add(user1)
    test_db.commit()
    
    # Try to create another user with the same username
    user2 = User(
        username="uniqueuser",  # Same username
        email="different@example.com",
        hashed_password="password"
    )
    
    # Should raise an integrity error
    with pytest.raises(IntegrityError):
        test_db.add(user2)
        test_db.commit()
        
    # Reset session
    test_db.rollback()
    
    # Try to create another user with the same email
    user3 = User(
        username="differentuser",
        email="unique@example.com",  # Same email
        hashed_password="password"
    )
    
    # Should raise an integrity error
    with pytest.raises(IntegrityError):
        test_db.add(user3)
        test_db.commit()


def test_user_model_defaults(test_db):
    """Test default values for User model."""
    # Create a minimal user
    user = User(
        username="defaultuser",
        email="default@example.com",
        hashed_password="password"
    )
    
    # Add to database
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    # Check default values
    assert user.full_name is None
    assert user.is_active is True  # Default should be True
    assert user.is_superuser is False  # Default should be False
    assert user.created_at is not None
    assert user.updated_at is not None 