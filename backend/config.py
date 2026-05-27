"""
Configuration for Kulima OS Backend API
"""
import os
import secrets
import logging
from pydantic_settings import BaseSettings
from typing import Optional

logger = logging.getLogger(__name__)


def _resolve_secret_key() -> str:
    """
    Resolve SECRET_KEY securely.
    Production: must be set via environment variable.
    Development: generates an ephemeral random key with a warning.
    """
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key
    # TODO(security): In production, SECRET_KEY must always be provided via env or KMS.
    logger.warning(
        "SECRET_KEY not found in environment. Generating ephemeral secret. "
        "This instance will be isolated — sessions will not persist across restarts."
    )
    return secrets.token_hex(32)


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    APP_NAME: str = "Kulima OS API"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Database Configuration
    # Set DATABASE_URL env var for production PostgreSQL, falls back to SQLite for local dev
    DATABASE_URL: str = "sqlite:///./kulima_os.db"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Security
    API_KEY: Optional[str] = None
    SECRET_KEY: str = _resolve_secret_key()
    
    # CORS
    # TODO(security): Replace wildcard with specific frontend origins in production
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
