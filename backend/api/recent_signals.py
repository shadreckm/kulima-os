"""
Simple recent signals endpoint used by frontend live feed polling.
"""
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import Signal
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/signals/recent")
async def get_recent_signals(response: Response, limit: int = 15, db: Session = Depends(get_db)):
    try:
        # Ensure no caching
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        # Fetch recent signals, ordered by newest first
        signals = db.query(Signal).order_by(Signal.timestamp.desc()).limit(limit).all()
        
        logger.info(f"Fetched {len(signals)} recent signals from database")
        
        result = []
        for s in signals:
            signal_dict = {
                'id': s.id,
                'zone': s.zone,
                'activity_type': s.activity_type,
                'activity': s.activity_type,  # Include both for compatibility
                'time_window': s.time_window,
                'timestamp': s.timestamp.isoformat() if s.timestamp else None,
                'source': s.source,
                'user_id': s.user_id,
                'original_text': s.original_text
            }
            result.append(signal_dict)
            logger.debug(f"Added signal {s.id} (activity: {s.activity_type}, zone: {s.zone})")
        
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error fetching recent signals: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}
