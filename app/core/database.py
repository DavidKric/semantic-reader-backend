"""
Database connection management for the application.

This module provides utilities for connecting to the database,
creating sessions, and managing database connections.
"""

import logging
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

logger = logging.getLogger(__name__)

# Check if DATABASE_URL is configured
if settings.DATABASE_URL:
    # Create SQLAlchemy engine with connection pooling
    engine = create_engine(
        settings.DATABASE_URL,
        **settings.get_db_connection_args()
    )
    
    # Create sessionmaker with the engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    logger.info(f"Database connection established to {settings.DATABASE_URL}")
else:
    logger.warning("DATABASE_URL not configured. Database functionality will be limited.")
    # Create a null engine for when database is not configured
    engine = None
    SessionLocal = None

# Create declarative base for SQLAlchemy models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Get a database session from the connection pool.
    
    Yields:
        Session: A SQLAlchemy session for database operations.
        
    Raises:
        RuntimeError: If database connection is not configured.
    """
    if SessionLocal is None:
        raise RuntimeError("Database connection is not configured")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 