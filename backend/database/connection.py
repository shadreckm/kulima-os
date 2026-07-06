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
        logger.warning("DATABASE_URL not set, using SQLite for development")
        return "sqlite:///./kulima_os.db"

    url = raw_url.strip()
    
    # Log the database type being configured (masked for security)
    if url.startswith("postgresql") or url.startswith("postgres"):
        masked_url = url
        if "@" in masked_url:
            parts = masked_url.split("@")
            prefix_parts = parts[0].split(":")
            if len(prefix_parts) >= 3:
                masked_url = f"{prefix_parts[0]}:{prefix_parts[1]}:****@{parts[1]}"
        logger.info(f"Configuring PostgreSQL connection: {masked_url}")
    else:
        logger.info(f"Configuring database connection: {url}")
    
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
        logger.info("Normalized postgres:// to postgresql://")
    
    if url.startswith("postgresql://") and "sslmode=" not in url:
        url = f"{url}?sslmode=require"
        logger.info("Added sslmode=require to PostgreSQL URL")
    
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
            connect_args={
                "connect_timeout": 10,  # 10 second timeout
                "options": "-c statement_timeout=30000"  # 30 second query timeout
            }
        )

    raise ValueError(f"Unsupported database URL scheme: {url}")


def _create_session_factory(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _safe_engine():
    url = _normalize_database_url(os.getenv("DATABASE_URL") or settings.DATABASE_URL)
    max_retries = 3
    last_error = None

    if url.startswith("postgresql"):
        logger.info(f"Attempting PostgreSQL connection (max {max_retries} retries)...")
        for attempt in range(1, max_retries + 1):
            try:
                engine = _build_engine(url)
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT version()"))
                    version = result.scalar()
                    logger.info(f"✅ PostgreSQL connection successful: {version}")
                logger.info("✅ OK DATABASE ENGINE: PostgreSQL")
                return engine
            except Exception as exc:
                last_error = exc
                logger.error(f"❌ PostgreSQL connection attempt {attempt}/{max_retries} failed: {exc}")
                if attempt < max_retries:
                    logger.info(f"Retrying in 2 seconds...")
                    time.sleep(2)
        
        # All PostgreSQL attempts failed
        logger.error(f"❌ PostgreSQL connection failed after {max_retries} attempts")
        logger.error(f"Last error: {last_error}")
        logger.warning("⚠️  FALLING BACK TO SQLITE - This should NOT happen in production!")
        logger.warning("⚠️  Check DATABASE_URL environment variable and network connectivity")
        
        fallback_url = "sqlite:///./kulima_os_fallback.db"
        fallback_engine = _build_engine(fallback_url)
        with fallback_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.warning(f"⚠️  Using SQLite fallback: {fallback_url}")
        return fallback_engine
    else:
        # SQLite path
        try:
            engine = _build_engine(url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ OK DATABASE ENGINE: SQLite")
            return engine
        except Exception as exc:
            last_error = exc
            logger.error(f"❌ SQLite connection failed: {exc}")
            raise


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
    from backend.database.evidence_models import Evidence, EvidenceTrustFactors, EvidenceLink, EvidenceAuditLog

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
