"""
Database connection management
Supports both SQLite (development) and PostgreSQL (production)
"""
from sqlalchemy import create_engine, text
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

        # Ensure SQLite schema upgrades (add missing columns safely)
        def _ensure_sqlite_schema():
            """
            For SQLite only: inspect table schema via PRAGMA and add missing
            columns (non-destructive). This uses raw SQL via SQLAlchemy's
            text() to run the PRAGMA and ALTER TABLE statements.
            """
            if not is_sqlite:
                return

            try:
                with engine.connect() as conn:
                    # Get existing columns for the signals table
                    res = conn.execute(text("PRAGMA table_info('signals')"))
                    cols = [row[1] for row in res.fetchall()]

                    if 'sector' not in cols:
                        logger.info("'sector' column missing from 'signals' table; adding it now")
                        conn.execute(text("ALTER TABLE signals ADD COLUMN sector TEXT NOT NULL DEFAULT ''"))
                        logger.info("Added 'sector' column to 'signals' table")
                    else:
                        logger.debug("'sector' column already present in 'signals' table")

                    if 'original_text' not in cols:
                        logger.info("'original_text' column missing from 'signals' table; adding it now")
                        conn.execute(text("ALTER TABLE signals ADD COLUMN original_text TEXT NOT NULL DEFAULT ''"))
                        logger.info("Added 'original_text' column to 'signals' table")
                    else:
                        logger.debug("'original_text' column already present in 'signals' table")

                    if 'source' not in cols:
                        logger.info("'source' column missing from 'signals' table; adding it now")
                        conn.execute(text("ALTER TABLE signals ADD COLUMN source TEXT NOT NULL DEFAULT 'web'"))
                        logger.info("Added 'source' column to 'signals' table")
                    else:
                        logger.debug("'source' column already present in 'signals' table")

                    if 'user_id' not in cols:
                        logger.info("'user_id' column missing from 'signals' table; adding it now")
                        conn.execute(text("ALTER TABLE signals ADD COLUMN user_id TEXT NOT NULL DEFAULT 'anonymous'"))
                        logger.info("Added 'user_id' column to 'signals' table")
                    else:
                        logger.debug("'user_id' column already present in 'signals' table")
            except Exception as e:
                logger.error(f"Failed to ensure sqlite schema: {e}")

        _ensure_sqlite_schema()

        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
