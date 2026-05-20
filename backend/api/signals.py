"""
Signal endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import Signal

router = APIRouter()


@router.post("/signal")
async def create_signal(signal_data: dict, db: Session = Depends(get_db)):
    """
    Receive activity input from WhatsApp or manual entry.
    
    Request body:
    {
      "zone": "MZUZU",
      "activity_type": "irrigation",
      "time_window": "morning",
      "timestamp": "2026-05-20T10:00:00Z",
      "source": "whatsapp",
      "user_id": "user_123"
    }
    """
    try:
        # Generate signal ID
        signal_id = f"sig_{uuid.uuid4().hex[:12]}"
        
        # Store signal in database
        signal = Signal(
            id=signal_id,
            zone=signal_data.get("zone"),
            activity_type=signal_data.get("activity_type"),
            time_window=signal_data.get("time_window"),
            timestamp=datetime.fromisoformat(signal_data.get("timestamp", datetime.utcnow().isoformat())),
            source=signal_data.get("source", "manual"),
            user_id=signal_data.get("user_id", "unknown")
        )
        db.add(signal)
        db.commit()
        
        print(f"Signal stored: {signal_id} - {signal_data.get('activity_type')} in {signal_data.get('zone')}")
        
        return {
            "status": "success",
            "signal_id": signal_id,
            "message": "Signal received and processed"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/{zone}")
async def get_signals(zone: str, limit: int = 100):
    """
    Get signals for a specific zone.
    """
    try:
        # TODO: Query database for signals in zone
        return {
            "zone": zone,
            "signals": [],
            "total": 0,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
