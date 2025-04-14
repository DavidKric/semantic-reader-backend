# Semantic Reader Backend

A FastAPI-based backend for the Semantic Reader application, following modern best practices for Python web development with uv package management.

## Project Overview

The Semantic Reader Backend provides API endpoints for document parsing, analysis, and semantic understanding. It uses FastAPI, SQLAlchemy, and follows clean architecture principles with proper separation of concerns.

## Project Structure

The project follows a modern, modular structure:

```
app/
├── api/                  # API routes and endpoints
│   ├── v1/               # API version 1
├── core/                 # Core application components
├── dependencies/         # Dependency injection system
├── models/               # Database models (SQLAlchemy)
├── schemas/              # Pydantic schemas for validation
├── services/             # Business logic
├── utils/                # Utility functions
```

See [app/README.md](app/README.md) for detailed information about the project structure.

## Installation

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - Modern Python package manager

### Setup

1. Clone the repository
   ```
   git clone <repository-url>
   cd semantic-reader-backend
   ```

2. Install dependencies with uv
   ```
   uv pip install -e ".[dev]"
   ```

3. Configure environment variables (copy from template)
   ```
   cp .env.example .env
   ```

4. Run the application
   ```
   python -m app.main
   ```

## Development

### Using Make Commands

The project includes a Makefile with common development tasks:

```
# Install production dependencies
make install

# Install development dependencies
make dev

# Run the application
make run

# Run tests
make test

# Run linting checks
make lint

# Format code
make format

# Clean build artifacts
make clean
```

### Database Migrations

The project uses Alembic for database migrations:

```
# Generate a new migration
make migrate message="your migration message"

# Upgrade to the latest migration
make upgrade
```

## Documentation

API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

[MIT License](LICENSE)

## Migration Guide

If you're transitioning from the previous project structure, see the [Migration Guide](docs/migration-guide.md) for detailed instructions. 