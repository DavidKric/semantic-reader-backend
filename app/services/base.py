"""
Base service class for implementing business logic.

This module provides a base service class that all other services can inherit from,
providing common functionality for database access and other operations.
"""

import logging
from datetime import datetime
from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from app.models.base import BaseModel

# Define generic type variables for model and ID
T = TypeVar('T', bound=BaseModel)
ID = TypeVar('ID')


class BaseService(Generic[T, ID]):
    """
    Base service class with common CRUD operations.
    
    Generic parameters:
        T: The model type this service operates on
        ID: The type of the model's ID field
    """
    
    def __init__(self, model: Type[T], db: Session):
        """
        Initialize the service with model class and database session.
        
        Args:
            model: The SQLAlchemy model class
            db: The database session
        """
        self.model = model
        self.db = db
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
    
    def get_by_id(self, id: ID) -> Optional[T]:
        """
        Get a model instance by ID.
        
        Args:
            id: The ID of the model to retrieve
            
        Returns:
            The model instance if found, None otherwise
        """
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self) -> List[T]:
        """
        Get all model instances.
        
        Returns:
            A list of all model instances
        """
        return self.db.query(self.model).all()
    
    def create(self, **data: Any) -> T:
        """
        Create a new model instance.
        
        Args:
            **data: Keyword arguments containing model data
            
        Returns:
            The created model instance
        """
        db_obj = self.model(**data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def update(self, id: ID, **data: Any) -> Optional[T]:
        """
        Update a model instance by ID.
        
        Args:
            id: The ID of the model to update
            **data: Keyword arguments containing model data to update
            
        Returns:
            The updated model instance if found, None otherwise
        """
        db_obj = self.get_by_id(id)
        if db_obj is None:
            return None
        
        for key, value in data.items():
            setattr(db_obj, key, value)
            
        # Update the updated_at timestamp
        db_obj.updated_at = datetime.utcnow()
            
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, id: ID) -> bool:
        """
        Delete a model instance by ID.
        
        Args:
            id: The ID of the model to delete
            
        Returns:
            True if the model was deleted, False if it wasn't found
        """
        db_obj = self.get_by_id(id)
        if db_obj is None:
            return False
        
        self.db.delete(db_obj)
        self.db.commit()
        return True 