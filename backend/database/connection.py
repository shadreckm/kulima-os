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
import time

logger = logging.getLogger(__name__)


def _normalize_database_url(raw_url: str | None) -> str:
    if not raw_url:
        logger.info("DATABASE_URL not set, using SQLite for development")
        return "sqlite:///./kulima_os.db"

    url = raw_url.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def _build_engine(url: str):
    if url.startswith("sqlite"):
        db_path = Path(url.replace("sqlite:///", ""))
        if db_path.parent != Path("."):
            db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using SQLite database: {db_path}")
        return create_engine(url, echo=settings.DATABASE_ECHO, connect_args={"check_same_thread": False})

    if url.startswith("postgresql"):
        logger.info("Using PostgreSQL database")
        return create_engine(
            url,
            echo=settings.DATABASE_ECHO,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_pre_ping=True,
        )

    raise ValueError(f"Unsupported database URL scheme: {url}")


def _create_session_factory(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _safe_engine():
    url = _normalize_database_url(os.getenv("DATABASE_URL") or settings.DATABASE_URL)
    try:
        engine = _build_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("OK DATABASE ENGINE")
        return engine
    except Exception as exc:
        logger.warning(f"Primary database connection failed: {exc}. Falling back to SQLite")
        fallback_url = "sqlite:///./kulima_os_fallback.db"
        fallback_engine = _build_engine(fallback_url)
        with fallback_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return fallback_engine


engine = _safe_engine()
SessionLocal = _create_session_factory(engine)


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
    Initialize database tables with graceful retry and SQLite fallback.
    """
    global engine, SessionLocal
    from backend.database.models import Base

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
            if insp.has_table('signals'):
                existing = {c['name'] for c in insp.get_columns('signals')}
                with engine.begin() as conn:
                    for col_name, col_def in required_columns.items():
                        if col_name not in existing:
                            logger.info(f"'{col_name}' column missing from 'signals' table; adding it now")
                            conn.execute(text(f"ALTER TABLE signals ADD COLUMN {col_name} {col_def}"))
                            logger.info(f"Added '{col_name}' column to 'signals' table")

            if insp.has_table('prospectuses'):
                existing_pros = {c['name'] for c in insp.get_columns('prospectuses')}
                if 'user_id' not in existing_pros:
                    logger.info("'user_id' column missing from 'prospectuses' table; adding it now")
                    with engine.begin() as conn:
                        conn.execute(text("ALTER TABLE prospectuses ADD COLUMN user_id TEXT NOT NULL DEFAULT 'anonymous'"))
                    logger.info("Added 'user_id' column to 'prospectuses' table")
        except Exception as e:
            logger.error(f"Failed to ensure schema: {e}")

    max_retries = 3
    retry_delay = 2
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Database initialization attempt {attempt}/{max_retries}...")
            if reset:
                logger.warning("Dropping all database tables...")
                Base.metadata.drop_all(bind=engine)

            logger.info("Creating database tables...")
            Base.metadata.create_all(bind=engine, checkfirst=True)
            _ensure_schema()

            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("OK DATABASE CONNECTION: verified")
            logger.info("Database initialization complete")
            return
        except Exception as e:
            last_error = e
            logger.warning(f"Database initialization attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(retry_delay)

    logger.error(f"Failed to connect to primary database after {max_retries} attempts: {last_error}")
    fallback_url = "sqlite:///./kulima_os_fallback.db"
    logger.warning(f"Falling back to local SQLite database: {fallback_url}")

    try:
        engine = _build_engine(fallback_url)
        SessionLocal = _create_session_factory(engine)
        logger.info("Initializing fallback SQLite database...")
        Base.metadata.create_all(bind=engine, checkfirst=True)
        _ensure_schema()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Fallback SQLite database initialized successfully")
    except Exception as fallback_err:
        logger.critical(f"SQLite fallback database initialization failed: {fallback_err}")
