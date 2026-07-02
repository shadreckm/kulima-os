from fastapi import APIRouter, Depends
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.database.connection import get_db
from backend.database import connection
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint with real database connectivity test"""
    db_status = "unhealthy"
    db_type = "unknown"
    db_version = None
    db_host = None
    
    try:
        # Perform a simple, low-overhead query to verify DB connection
        db.execute(text("SELECT 1"))
        db_status = "connected"
        
        # Detect database type from engine URL
        engine_url = str(connection.engine.url)
        if "postgresql" in engine_url or "postgres" in engine_url:
            db_type = "postgresql"
            # Get PostgreSQL version
            try:
                result = db.execute(text("SELECT version()"))
                db_version = result.scalar()
            except Exception as e:
                logger.warning(f"Could not get PostgreSQL version: {e}")
            
            # Extract host from URL
            if "@" in engine_url:
                host_part = engine_url.split("@")[1]
                db_host = host_part.split("/")[0].split(":")[0]
        elif "sqlite" in engine_url:
            db_type = "sqlite"
            db_version = "SQLite (local file)"
            db_host = "local"
        
    except Exception as e:
        logger.error(f"Health check failed database verification: {e}")
        db_status = f"error: {str(e)}"

    # Get DB engine URL and mask user/password for safety
    _display_url = str(connection.engine.url)
    if "@" in _display_url:
        parts = _display_url.split("@")
        prefix = parts[0].split(":")
        if len(prefix) >= 3:
            _display_url = f"{prefix[0]}:{prefix[1]}:****@{parts[1]}"

    status = "healthy" if db_status == "connected" else "unhealthy"
    success = status == "healthy"
    
    # Add warning if SQLite is detected when PostgreSQL is expected
    warning = None
    if db_type == "sqlite" and db_status == "connected":
        warning = "⚠️  Using SQLite fallback - PostgreSQL connection may have failed"

    response = {
        "success": success,
        "status": status,
        "database": db_status,
        "database_type": db_type,
        "database_engine": _display_url,
        "engines": "operational" if success else "degraded",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if db_host:
        response["database_host"] = db_host
    if db_version:
        response["database_version"] = db_version
    if warning:
        response["warning"] = warning
    
    return response
