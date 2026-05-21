"""
Signal endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Optional
import uuid
import logging
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import Signal
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


class SignalCreate(BaseModel):
    """Pydantic model for signal creation validation"""
    zone: str = Field(..., min_length=1, description="Zone identifier")
    activity_type: str = Field(..., min_length=1, description="Activity type")
    time_window: str = Field(..., min_length=1, description="Time window (morning/afternoon/evening)")
    timestamp: Optional[str] = Field(None, description="ISO format timestamp")
    source: str = Field(default="manual", description="Signal source")
    user_id: Optional[str] = Field(default="anonymous", description="User identifier")


@router.post("/signal")
async def create_signal(signal_data: SignalCreate, db: Session = Depends(get_db)):
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
        
        # Standardize zone to uppercase
        zone = signal_data.zone.upper()
        
        # Parse timestamp with validation
        try:
            if signal_data.timestamp:
                timestamp = datetime.fromisoformat(signal_data.timestamp)
            else:
                timestamp = datetime.utcnow()
        except ValueError:
            logger.warning(f"Invalid timestamp format for signal {signal_id}, using current time")
            timestamp = datetime.utcnow()
        
        # Store signal in database
        signal = Signal(
            id=signal_id,
            zone=zone,
            activity_type=signal_data.activity_type,
            time_window=signal_data.time_window,
            timestamp=timestamp,
            source=signal_data.source,
            user_id=signal_data.user_id or "anonymous"
        )
        db.add(signal)
        db.commit()
        
        logger.info(f"Signal stored: {signal_id} - {signal_data.activity_type} in {zone}")
        
        return {
            "status": "success",
            "data": {
                "signal_id": signal_id,
                "message": "Signal received and processed"
            }
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error storing signal: {str(e)}")
        return {
            "status": "error",
            "data": {
                "error": str(e)
            }
        }


@router.get("/signals/{zone}")
async def get_signals(zone: str, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get signals for a specific zone.
    """
    try:
        # Query database for signals in zone
        zone_upper = zone.upper()
        signals = db.query(Signal).filter(Signal.zone == zone_upper).limit(limit).all()
        
        signal_list = []
        for signal in signals:
            signal_list.append({
                "id": signal.id,
                "zone": signal.zone,
                "activity_type": signal.activity_type,
                "time_window": signal.time_window,
                "timestamp": signal.timestamp.isoformat(),
                "source": signal.source,
                "user_id": signal.user_id,
                "created_at": signal.created_at.isoformat()
            })
        
        logger.info(f"Fetched {len(signal_list)} signals for zone {zone}")
        
        return {
            "status": "success",
            "data": {
                "zone": zone,
                "signals": signal_list,
                "total": len(signal_list),
                "limit": limit
            }
        }
    except Exception as e:
        logger.error(f"Error fetching signals: {str(e)}")
        return {
            "status": "error",
            "data": {
                "error": str(e)
            }
        }
