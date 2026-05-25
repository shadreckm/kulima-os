"""
Database connection management
Supports both SQLite (development) and PostgreSQL (production)
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path
from backend.config import settings
import logging

logger = logging.getLogger(__name__)

# Determine database type
is_postgresql = "postgresql" in settings.DATABASE_URL
is_sqlite = "sqlite" in settings.DATABASE_URL

# SQLite-specific setup
if is_sqlite:
    db_path = Path(settings.DATABASE_URL.replace("sqlite:///", ""))
    if db_path.parent != Path("."):
        db_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Using SQLite database: {db_path}")

# PostgreSQL-specific setup
if is_postgresql:
    logger.info(f"Using PostgreSQL database")

# Create database engine with appropriate configuration
if is_sqlite:
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        connect_args={"check_same_thread": False}
    )
elif is_postgresql:
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True  # Verify connections before using
    )
else:
    raise ValueError(f"Unsupported database URL scheme: {settings.DATABASE_URL}")

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
        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
