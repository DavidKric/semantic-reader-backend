# Semantic Reader Backend - Project Structure

This document outlines the project structure of the Semantic Reader Backend application, which follows modern FastAPI and uv best practices.

## Directory Structure

```
app/
├── api/                  # API routes and endpoints
│   ├── v1/               # API version 1
│   │   ├── health.py     # Health check endpoints
│   │   └── ...           # Other API modules
│   └── __init__.py       # API package initialization
├── core/                 # Core application components
│   ├── config.py         # Configuration and settings
│   ├── database.py       # Database connection management
│   └── __init__.py       # Core package initialization
├── dependencies/         # Dependency injection system
│   ├── database.py       # Database session dependencies
│   └── __init__.py       # Dependencies package initialization
├── models/               # Database models (SQLAlchemy)
│   ├── base.py           # Base model class
│   └── __init__.py       # Models package initialization
├── schemas/              # Pydantic schemas for validation
│   ├── base.py           # Base schema classes
│   └── __init__.py       # Schemas package initialization
├── services/             # Business logic
│   ├── base.py           # Base service class
│   └── __init__.py       # Services package initialization
├── utils/                # Utility functions
│   ├── logging.py        # Logging utilities
│   └── __init__.py       # Utils package initialization
├── main.py               # Application initialization
└── __init__.py           # App package initialization
```

## Component Descriptions

### API (`app/api/`)

Contains all API endpoints organized by version. Each resource has its own module with route definitions. The `v1` directory contains endpoints for API version 1.

### Core (`app/core/`)

Core components that are used throughout the application:

- `config.py`: Application settings and configuration loaded from environment variables using Pydantic
- `database.py`: Database connection management and session creation

### Dependencies (`app/dependencies/`)

Dependency injection system for FastAPI routes. Contains reusable dependencies that can be injected into routes.

### Models (`app/models/`)

SQLAlchemy ORM models that define the database schema. The `base.py` module contains a base model class with common fields like id, created_at, and updated_at.

### Schemas (`app/schemas/`)

Pydantic models for request/response validation, serialization, and documentation. The `base.py` module contains base schema classes and utilities.

### Services (`app/services/`)

Business logic layer that operates on models and is used by API routes. The `base.py` module contains a base service class with common CRUD operations.

### Utils (`app/utils/`)

Utility functions and helpers used throughout the application.

### Main (`app/main.py`)

Application initialization, middleware configuration, and entrypoint.

## Usage

This structure follows modern FastAPI and uv best practices, providing:

1. Clear separation of concerns
2. Proper dependency injection
3. Modular and maintainable code
4. API versioning
5. Reusable components
6. Clean architecture principles

When adding new features:

1. Create models in `app/models/`
2. Create schemas in `app/schemas/`
3. Implement business logic in `app/services/`
4. Define API endpoints in `app/api/v1/` 