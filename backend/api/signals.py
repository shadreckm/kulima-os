"""
Signal endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from datetime import datetime
from typing import Optional
import uuid
import logging
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import Signal
from backend.schemas.requests import SignalCreate, SignalsQuery
from core.coordination.multi_sector_coordinator import MultiSectorCoordinator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize multi-sector coordinator
sector_coordinator = MultiSectorCoordinator()


@router.post("/signal")
async def create_signal(request: Request, db: Session = Depends(get_db)):
    """
    Receive activity input from WhatsApp or manual entry.

    Accepts either structured JSON or a `raw_text` field which will be normalized server-side.
    """
    try:
        payload = {}
        try:
            payload = await request.json()
        except Exception:
            # If the client doesn't send JSON, return an error
            return {"status": "error", "message": "Invalid JSON payload"}

        # Generate signal ID
        signal_id = f"sig_{uuid.uuid4().hex[:12]}"

        # If raw_text is provided, normalize it
        if 'raw_text' in payload and payload.get('raw_text'):
            from backend.utils.signal_normalizer import normalize_signal_text
            normalized = normalize_signal_text(payload.get('raw_text'))
            zone = (payload.get('zone') or normalized.get('zone') or 'UNKNOWN').upper()
            activity = normalized.get('activity_type') or 'unknown'
            time_window = normalized.get('time_window') or 'unknown'
            original_text = normalized.get('original_text', payload.get('raw_text')) or ''
        else:
            # Expect structured fields
            zone = (payload.get('zone') or 'UNKNOWN').upper()
            activity = payload.get('activity_type') or 'unknown'
            time_window = payload.get('time_window') or 'unknown'
            original_text = payload.get('original_text') or ''

        # Parse timestamp with validation
        try:
            if payload.get('timestamp'):
                timestamp = datetime.fromisoformat(payload.get('timestamp').replace('Z', '+00:00'))
            else:
                timestamp = datetime.utcnow()
        except ValueError:
            logger.warning(f"Invalid timestamp format for signal {signal_id}, using current time")
            timestamp = datetime.utcnow()

        # Classify sector using multi-sector coordinator with safe fallback
        try:
            sector = sector_coordinator.classify_sector(activity)
            if not sector:
                sector = "general"
        except Exception as e:
            logger.warning(f"Sector classification failed: {e}; defaulting to 'general'")
            sector = "general"

        # Store signal in database (include original_text)
        signal = Signal(
            id=signal_id,
            zone=zone,
            activity_type=activity,
            sector=sector,
            time_window=time_window,
            timestamp=timestamp,
            source=payload.get('source') or "web",
            user_id=payload.get('user_id') if payload.get('user_id') else "anonymous",
            original_text=original_text or ''
        )
        db.add(signal)
        db.commit()
        db.refresh(signal)

        print(f"✅ SIGNAL STORED: {signal.id} {signal.activity_type} {signal.zone}")
        logger.info(f"✅ SIGNAL STORED: {signal.id} {signal.activity_type} {signal.zone}")

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
            "message": str(e),
            "details": {
                "error": str(e)
            }
        }


@router.get("/signals/{zone}")
async def get_signals(
    zone: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    activity_type: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get signals for a specific zone with pagination and filtering.
    
    Query parameters:
    - limit: Maximum number of results (1-1000, default 100)
    - offset: Number of results to skip (default 0)
    - activity_type: Filter by activity type (optional)
    - date_from: Filter from date (ISO format, optional)
    - date_to: Filter to date (ISO format, optional)
    """
    try:
        # Validate zone
        zone_upper = zone.upper()
        
        # Build query
        query = db.query(Signal).filter(Signal.zone == zone_upper)
        
        # Apply filters
        if activity_type:
            query = query.filter(Signal.activity_type == activity_type.lower())
        
        if date_from:
            try:
                from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                query = query.filter(Signal.timestamp >= from_date)
            except ValueError:
                logger.warning(f"Invalid date_from format: {date_from}")
        
        if date_to:
            try:
                to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                query = query.filter(Signal.timestamp <= to_date)
            except ValueError:
                logger.warning(f"Invalid date_to format: {date_to}")
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        signals = query.order_by(Signal.timestamp.desc()).offset(offset).limit(limit).all()
        
        # Build response
        signal_list = []
        for signal in signals:
            signal_list.append({
                "id": signal.id,
                "zone": signal.zone,
                "activity_type": signal.activity_type,
                "sector": signal.sector,
                "time_window": signal.time_window,
                "timestamp": signal.timestamp.isoformat(),
                "source": signal.source,
                "user_id": signal.user_id,
                "created_at": signal.created_at.isoformat()
            })
        
        logger.info(f"Fetched {len(signal_list)} signals for zone {zone} (total: {total})")
        
        return {
            "status": "success",
            "data": {
                "zone": zone_upper,
                "signals": signal_list,
                "pagination": {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total
                }
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
