from fastapi import APIRouter, Depends
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.database.connection import get_db, engine
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint with real database connectivity test"""
    db_status = "unhealthy"
    try:
        # Perform a simple, low-overhead query to verify DB connection
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Health check failed database verification: {e}")
        db_status = f"error: {str(e)}"

    # Get DB engine URL and mask user/password for safety
    _display_url = str(engine.url)
    if "@" in _display_url:
        parts = _display_url.split("@")
        prefix = parts[0].split(":")
        if len(prefix) >= 3:
            _display_url = f"{prefix[0]}:{prefix[1]}:****@{parts[1]}"

    status = "healthy" if db_status == "connected" else "unhealthy"
    success = status == "healthy"

    return {
        "success": success,
        "status": status,
        "database": db_status,
        "database_engine": _display_url,
        "engines": "operational" if success else "degraded",
        "timestamp": datetime.utcnow().isoformat()
    }
