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
    DATABASE_URL: str = "sqlite:///./kulima_os.db"
    DATABASE_ECHO: bool = False
    
    # Security
    API_KEY: Optional[str] = None
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # File Storage
    ARTIFACTS_DIR: str = "./artifacts"
    
    # WhatsApp Integration
    WHATSAPP_WEBHOOK_URL: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
