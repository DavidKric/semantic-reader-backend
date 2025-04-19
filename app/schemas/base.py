"""
Base schemas and utilities for Pydantic models.

This module provides base schema classes and utilities that are used
throughout the application for request/response validation.
"""

from datetime import datetime
from typing import Generic, List, TypeVar

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema for all Pydantic models."""
    
    model_config = ConfigDict(
        # Allow by alias and by name
        populate_by_name=True,
        
        # Transform from camelCase to snake_case and vice versa
        alias_generator=lambda s: ''.join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(s.split('_'))
        ),
        
        # Validate assignment
        validate_assignment=True,
        
        # Extra attributes
        extra="ignore",
        
        # JSON serialization of datetime objects
        json_encoders={
            datetime: lambda dt: dt.isoformat(),
        }
    )


# Define generic type variables for pagination
T = TypeVar('T')


class PaginationParams(BaseSchema):
    """Query parameters for pagination."""
    
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(10, ge=1, le=100, description="Items per page")
    
    def get_skip(self) -> int:
        """Calculate skip value for SQL queries."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated response wrapper for any schema type."""
    
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int
    
    @classmethod
    def create(
        cls, 
        items: List[T], 
        total: int, 
        params: PaginationParams
    ) -> "PaginatedResponse[T]":
        """Create a paginated response from items, total count, and pagination params."""
        pages = (total + params.page_size - 1) // params.page_size if total > 0 else 0
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=pages
        ) 