"""
Configuration settings for the application.

This module loads settings from environment variables and provides them
as a single importable settings object. Using pydantic_settings for type validation.
"""

import os
from typing import List, Dict, Any, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable loading."""
    
    # Application information
    APP_NAME: str = "Semantic Reader Backend"
    APP_VERSION: str = "0.1.0"
    API_VERSION: str = "v1"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS_COUNT: int = 1
    DEBUG_MODE: bool = False
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # CORS settings
    ALLOWED_ORIGINS_STR: str = "*"
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # UI settings
    ENABLE_UI: bool = True
    
    # Model settings
    MODEL: str = "claude-3-7-sonnet-20250219"
    PERPLEXITY_MODEL: str = "sonar-pro"
    MAX_TOKENS: int = 64000
    TEMPERATURE: float = 0.2
    
    # Default Task Settings
    DEFAULT_SUBTASKS: int = 5
    DEFAULT_PRIORITY: str = "medium"
    PROJECT_NAME: str = "papermage-docling"
    
    # Document processing settings
    OCR_ENABLED: bool = False
    OCR_LANGUAGE: str = "eng"
    DETECT_RTL: bool = True
    ALLOWED_EXTENSIONS_STR: str = "pdf,docx,txt"
    MAX_FILE_SIZE_MB: int = 50
    
    # Database settings
    DATABASE_URL: Optional[str] = None
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False
    
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """Parse ALLOWED_ORIGINS_STR into a list"""
        origins = self.ALLOWED_ORIGINS_STR
        
        # Handle comma-separated format
        if "," in origins:
            return [origin.strip() for origin in origins.split(",")]
        
        # Handle single value
        return [origins]
    
    @property
    def ALLOWED_EXTENSIONS(self) -> List[str]:
        """Parse ALLOWED_EXTENSIONS_STR into a list"""
        extensions = self.ALLOWED_EXTENSIONS_STR
        
        # Handle comma-separated format
        if "," in extensions:
            return [ext.strip() for ext in extensions.split(",")]
        
        # Handle single value
        return [extensions]
    
    # Temporarily comment out validators for debugging
    # @validator("LOG_LEVEL")
    # def validate_log_level(cls, v: str) -> str:
    #     """Validate that LOG_LEVEL is a valid logging level."""
    #     allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    #     if v.upper() not in allowed_levels:
    #         raise ValueError(f"LOG_LEVEL must be one of {allowed_levels}")
    #     return v.upper()
    
    def get_db_connection_args(self) -> Dict[str, Any]:
        """Get database connection arguments for SQLAlchemy."""
        return {
            "pool_size": self.DB_POOL_SIZE,
            "max_overflow": self.DB_MAX_OVERFLOW,
            "echo": self.DB_ECHO,
        }
    
    model_config = SettingsConfigDict(
        # Use .env file but allow env vars to override
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Create settings instance (singleton)
settings = Settings() 