"""
Configuration for Kulima OS Backend API
"""
import os
import secrets
import logging
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional, Union

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent


def _load_env_file() -> None:
    """Load environment variables from the repository .env file when present."""
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        logger.warning(f".env file not found at {env_path}")
        return

    loaded_vars = []
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)
        loaded_vars.append(key)
    
    if loaded_vars:
        logger.info(f"Loaded environment variables from .env: {', '.join(loaded_vars)}")
    
    # Explicitly log DATABASE_URL status (masked for security)
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        if "postgresql" in db_url or "postgres" in db_url:
            # Mask password in log
            masked_url = db_url
            if "@" in masked_url:
                parts = masked_url.split("@")
                prefix_parts = parts[0].split(":")
                if len(prefix_parts) >= 3:
                    masked_url = f"{prefix_parts[0]}:{prefix_parts[1]}:****@{parts[1]}"
            logger.info(f"DATABASE_URL loaded: {masked_url}")
        else:
            logger.info(f"DATABASE_URL loaded: {db_url}")
    else:
        logger.warning("DATABASE_URL not found in environment - will use SQLite fallback")


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


# CRITICAL: Load .env file BEFORE Settings class is instantiated
_load_env_file()


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    APP_NAME: str = "Kulima OS API"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Database Configuration
    # PRODUCTION: DATABASE_URL must be set to PostgreSQL connection string
    # DEVELOPMENT: Falls back to SQLite if DATABASE_URL not set
    DATABASE_URL: Optional[str] = None
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Security
    API_KEY: Optional[str] = None
    SECRET_KEY: str = _resolve_secret_key()
    
    # CORS
    # TODO(security): Replace wildcard with specific frontend origins in production
    # Accepts either a comma-separated string or a list
    CORS_ORIGINS: Union[str, list[str]] = ["*"]
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from environment variable (string or list)"""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Handle comma-separated string
            origins = [origin.strip() for origin in v.split(",") if origin.strip()]
            return origins if origins else ["*"]
        return ["*"]
    
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
        env_file = str(ROOT_DIR / ".env")
        case_sensitive = True


settings = Settings()
