# Migration Guide: Restructuring to Modern FastAPI Architecture

This guide outlines how to migrate existing code from the old project structure to the new architecture that follows modern FastAPI and uv best practices.

## Overview of Changes

The project has been restructured to follow a clean, modular architecture with clear separation of concerns:

- **Old Structure**: Flat structure with mixed concerns and limited organization
- **New Structure**: Modular structure with clear separation between API routes, business logic, and data models

## Migration Steps

### 1. API Routes Migration

**Old Location:** `app/api/*.py`  
**New Location:** `app/api/v1/*.py`

Steps:
1. Move route handlers to the appropriate module in `app/api/v1/`
2. Update imports to use the new structure
3. Use dependency injection for services and database sessions
4. Update route handlers to use Pydantic schemas for request/response validation

Example:

```python
# Old
@router.get("/items/{item_id}")
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# New
@router.get("/items/{item_id}", response_model=schemas.ItemResponse)
def get_item(
    item_id: int, 
    item_service: ItemService = Depends(get_item_service)
):
    item = item_service.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
```

### 2. Database Models Migration

**Old Location:** Mixed in various files  
**New Location:** `app/models/*.py`

Steps:
1. Move SQLAlchemy models to the appropriate module in `app/models/`
2. Update models to inherit from the base model class
3. Add proper type hints and documentation
4. Update imports throughout the codebase

Example:

```python
# Old
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    
# New
from app.models.base import BaseModel

class Item(BaseModel):
    """Item model representing a product or service."""
    
    name: Column = Column(String, index=True)
    description: Column = Column(String)
    # Note: id, created_at, and updated_at are inherited from BaseModel
```

### 3. Configuration Migration

**Old Location:** `app/config.py`  
**New Location:** `app/core/config.py`

Steps:
1. Move configuration to `app/core/config.py`
2. Use Pydantic's `BaseSettings` for configuration
3. Update imports throughout the codebase

### 4. Creating Pydantic Schemas

**Old Location:** Mixed with routes or missing  
**New Location:** `app/schemas/*.py`

Steps:
1. Create appropriate schemas for request/response models
2. Add validation rules and documentation
3. Use the schemas in API routes

Example:

```python
# In app/schemas/item.py
from app.schemas.base import BaseSchema

class ItemBase(BaseSchema):
    """Base schema for Item."""
    
    name: str
    description: str = None

class ItemCreate(ItemBase):
    """Schema for creating an Item."""
    pass

class ItemResponse(ItemBase):
    """Schema for Item response."""
    
    id: int
    created_at: datetime
    updated_at: datetime
```

### 5. Creating Services

**Old Location:** Business logic mixed with routes  
**New Location:** `app/services/*.py`

Steps:
1. Extract business logic from route handlers to service classes
2. Implement service methods for each operation
3. Use dependency injection to provide services to routes

Example:

```python
# In app/services/item_service.py
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.item import Item
from app.services.base import BaseService

class ItemService(BaseService[Item, int]):
    """Service for handling Item operations."""
    
    def __init__(self, db: Session):
        super().__init__(Item, db)
    
    def get_by_name(self, name: str) -> Optional[Item]:
        """Get an item by name."""
        return self.db.query(self.model).filter(self.model.name == name).first()
```

### 6. Dependency Injection

**Old Location:** Ad-hoc in route handlers  
**New Location:** `app/dependencies/*.py`

Steps:
1. Create reusable dependencies in the dependencies package
2. Implement factory functions for services
3. Update route handlers to use the dependencies

Example:

```python
# In app/dependencies/services.py
from fastapi import Depends
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.services.item_service import ItemService

def get_item_service(db: Session = Depends(get_db)) -> ItemService:
    """Dependency for ItemService."""
    return ItemService(db)
```

## Testing the Migration

After completing the migration:

1. Run the application with `python -m app.main`
2. Verify that all endpoints work as expected
3. Check the API documentation at `/docs`
4. Validate that the application runs correctly with uv

## Benefits of the New Structure

- **Maintainability**: Clean separation of concerns makes the code easier to maintain
- **Testability**: Components are isolated and can be tested independently
- **Scalability**: Modular architecture makes it easier to add new features
- **Readability**: Clear organization makes the codebase easier to understand
- **Performance**: uv's optimized dependency management improves build and runtime performance

## Additional Resources

For more information:
- See the [app/README.md](../app/README.md) for details on the new structure
- Read the [FastAPI documentation](https://fastapi.tiangolo.com/tutorial/bigger-applications/) on larger applications
- Explore the [uv documentation](https://docs.astral.sh/uv/) for Python package management 