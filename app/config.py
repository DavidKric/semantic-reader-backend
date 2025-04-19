"""
Configuration settings for the application.

This module loads settings from environment variables and provides them
as a single importable settings object.
"""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
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
    
    # CORS settings as a string to avoid parsing issues
    ALLOWED_ORIGINS_STR: str = "*"
    
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """Parse ALLOWED_ORIGINS_STR into a list"""
        origins = self.ALLOWED_ORIGINS_STR
        
        # Handle comma-separated format
        if "," in origins:
            return [origin.strip() for origin in origins.split(",")]
        
        # Handle single value
        return [origins]
    
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
    
    @property
    def ALLOWED_EXTENSIONS(self) -> List[str]:
        """Parse ALLOWED_EXTENSIONS_STR into a list"""
        extensions = self.ALLOWED_EXTENSIONS_STR
        
        # Handle comma-separated format
        if "," in extensions:
            return [ext.strip() for ext in extensions.split(",")]
        
        # Handle single value
        return [extensions]
    
    model_config = SettingsConfigDict(
        # Don't use .env files at all, to avoid any confusion
        env_file=None,
        case_sensitive=True
    )


# Create settings instance
settings = Settings() 