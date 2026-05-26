"""
Configuration for Kulima OS Backend API
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    APP_NAME: str = "Kulima OS API"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    # Database Configuration
    # Set DATABASE_URL env var for production PostgreSQL, falls back to SQLite for local dev
    DATABASE_URL: str = "sqlite:///./kulima_os.db"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Security
    API_KEY: Optional[str] = None
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # File Storage
    ARTIFACTS_DIR: str = "./artifacts"
    PROSPECTUS_DIR: str = "./prospectuses"
    
    # WhatsApp Integration
    WHATSAPP_WEBHOOK_URL: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Caching
    CACHE_TTL_SUMMARY: int = 300  # 5 minutes
    CACHE_TTL_PATTERNS: int = 900  # 15 minutes
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
