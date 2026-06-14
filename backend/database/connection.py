"""
Database connection management
Supports both SQLite (development) and PostgreSQL (production)
"""
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path
from backend.config import settings
import logging
import os

logger = logging.getLogger(__name__)

# Resolve DATABASE_URL — Render provides it without the dialect prefix sometimes
_raw_url = settings.DATABASE_URL

# Fallback: use SQLite if DATABASE_URL not set
if not _raw_url:
    _raw_url = "sqlite:///./kulima_os.db"
    logger.info("DATABASE_URL not set, using SQLite for development")

if _raw_url.startswith("postgres://"):
    _raw_url = _raw_url.replace("postgres://", "postgresql://", 1)

# Determine database type
is_postgresql = "postgresql" in _raw_url
is_sqlite = "sqlite" in _raw_url

# SQLite-specific setup
if is_sqlite:
    db_path = Path(_raw_url.replace("sqlite:///", ""))
    if db_path.parent != Path("."):
        db_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Using SQLite database: {db_path}")

# PostgreSQL-specific setup
if is_postgresql:
    logger.info("Using PostgreSQL database")

# Create database engine with appropriate configuration
if is_sqlite:
    engine = create_engine(
        _raw_url,
        echo=settings.DATABASE_ECHO,
        connect_args={"check_same_thread": False}
    )
elif is_postgresql:
    engine = create_engine(
        _raw_url,
        echo=settings.DATABASE_ECHO,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True
    )
else:
    raise ValueError(f"Unsupported database URL scheme: {_raw_url}")

# Log the database engine being used (mask password for security)
_display_url = str(engine.url)
if "@" in _display_url:
    # Mask password: postgresql://user:****@host:5432/db
    parts = _display_url.split("@")
    prefix = parts[0].split(":")
    if len(prefix) >= 3:
        _display_url = f"{prefix[0]}:{prefix[1]}:****@{parts[1]}"
logger.info(f"OK DATABASE ENGINE: {_display_url}")

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency for getting database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(reset: bool = False):
    """
    Initialize database tables
    
    Args:
        reset: If True, drop all tables and recreate them. Use with caution.
    """
    from backend.database.models import Base
    
    try:
        if reset:
            logger.warning("Dropping all database tables...")
            Base.metadata.drop_all(bind=engine)
        
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine, checkfirst=True)

        # Ensure schema upgrades (add missing columns safely)
        def _ensure_schema():
            """Inspect table schema and add missing columns (non-destructive)."""
            required_columns = {
                'sector': "TEXT NOT NULL DEFAULT ''",
                'original_text': "TEXT NOT NULL DEFAULT ''",
                'source': "TEXT NOT NULL DEFAULT 'web'",
                'user_id': "TEXT NOT NULL DEFAULT 'anonymous'",
            }
            try:
                insp = inspect(engine)
                if not insp.has_table('signals'):
                    return
                existing = {c['name'] for c in insp.get_columns('signals')}
                with engine.begin() as conn:
                    for col_name, col_def in required_columns.items():
                        if col_name not in existing:
                            logger.info(f"'{col_name}' column missing from 'signals' table; adding it now")
                            conn.execute(text(f"ALTER TABLE signals ADD COLUMN {col_name} {col_def}"))
                            logger.info(f"Added '{col_name}' column to 'signals' table")
            except Exception as e:
                logger.error(f"Failed to ensure schema: {e}")

        _ensure_schema()

        # Verify database connectivity
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("OK DATABASE CONNECTION: verified")

        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
