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

@router.get("/recent-signals")
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
            activity = s.activity_type or 'unknown'
            signal_dict = {
                'id': s.id,
                'zone': s.zone or 'UNKNOWN',
                'activity_type': activity,
                'activity': activity,
                'time_window': s.time_window or 'unknown',
                'timestamp': s.timestamp.isoformat() if s.timestamp else None,
                'source': s.source or 'web',
                'original_text': s.original_text or '',
                'created_at': s.created_at.isoformat() if s.created_at else None
            }
            result.append(signal_dict)
        
        logger.info(f"RECENT SIGNALS: {[{'id': r['id'], 'activity_type': r['activity_type'], 'zone': r['zone']} for r in result]}")
        
        return {"success": True, "status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error fetching recent signals: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "status": "error", "message": str(e)}
