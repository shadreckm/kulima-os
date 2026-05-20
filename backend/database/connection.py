"""
Database connection management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path
from backend.config import settings

# Ensure database directory exists
db_path = Path(settings.DATABASE_URL.replace("sqlite:///", ""))
if db_path.parent != Path("."):
    db_path.parent.mkdir(parents=True, exist_ok=True)

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

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
    
    if reset:
        print("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
    
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine, checkfirst=True)
    print("Database initialization complete.")
