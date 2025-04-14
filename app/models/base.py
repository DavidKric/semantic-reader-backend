"""
Base model class with common fields and functionality.

This module provides a base model class that all other models can inherit from,
providing common fields like id, created_at, updated_at, and shared functionality.
"""

import datetime
from typing import Any, Dict

from sqlalchemy import Column, DateTime, func, Integer
from sqlalchemy.ext.declarative import declared_attr

from app.core.database import Base


class BaseModel(Base):
    """
    Base model class that all other models should inherit from.
    
    Provides common fields and functionality for all models.
    """
    
    # Set __abstract__ to True so this model isn't created as a table
    __abstract__ = True
    
    # Primary key column
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Timestamps for created_at and updated_at
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Generate __tablename__ automatically based on class name
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name automatically from class name."""
        return cls.__name__.lower()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def __repr__(self) -> str:
        """String representation of the model."""
        values = ", ".join(
            f"{column.name}={getattr(self, column.name)!r}"
            for column in self.__table__.columns
        )
        return f"{self.__class__.__name__}({values})" 