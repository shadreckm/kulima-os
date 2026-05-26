"""
Simple recent signals endpoint used by frontend live feed polling.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import Signal
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/signals/recent")
async def get_recent_signals(limit: int = 15, db: Session = Depends(get_db)):
    try:
        signals = db.query(Signal).order_by(Signal.timestamp.desc()).limit(limit).all()
        result = []
        for s in signals:
            result.append({
                'id': s.id,
                'zone': s.zone,
                'activity_type': s.activity_type,
                'time_window': s.time_window,
                'timestamp': s.timestamp.isoformat(),
                'source': s.source,
                'user_id': s.user_id,
                'original_text': s.original_text
            })
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error fetching recent signals: {e}")
        return {"status": "error", "message": str(e)}
