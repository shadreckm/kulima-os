"""
Signal endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from datetime import datetime, timedelta
from typing import Optional
import uuid
import logging
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import Signal
from backend.schemas.requests import SignalRequest, SignalCreate, SignalsQuery
from backend.services.external_signals import normalize_signal_source
from backend.utils.signal_validator import validate_signal_input, is_duplicate_signal
from core.coordination.multi_sector_coordinator import MultiSectorCoordinator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize multi-sector coordinator
sector_coordinator = MultiSectorCoordinator()


@router.post("/signal")
async def create_signal(request: SignalRequest, db: Session = Depends(get_db)):
    """
    Receive activity input from WhatsApp or manual entry.

    Accepts either structured JSON or a `raw_text` field which will be normalized server-side.
    """
    try:
        # Generate signal ID
        signal_id = f"sig_{uuid.uuid4().hex[:12]}"

        # If raw_text is provided, normalize via NLP pipeline
        is_voice = (request.source or "").lower() in ("voice", "speech", "microphone")
        if request.raw_text:
            zone_hint = (request.zone or "MZUZU").upper()
            accepted, parsed, reason = validate_signal_input(
                request.raw_text, zone=zone_hint, is_voice=is_voice
            )
            if not accepted:
                logger.info(f"Signal rejected: {reason}")
                return {
                    "success": True,
                    "status": "success",
                    "data": {
                        "signal_id": None,
                        "message": f"Signal not recorded: {reason.replace('_', ' ')}",
                        "rejected": True,
                        "reason": reason,
                    }
                }
            zone = (request.zone or parsed.get('zone') or 'MZUZU').upper()
            activity = parsed.get('activity_type') or request.activity_type or 'unknown'
            time_window = parsed.get('time_window') or request.time_window or 'unknown'
            original_text = parsed.get('original_text', request.raw_text) or ''

            if is_duplicate_signal(db, zone, activity, time_window, parsed.get('normalized_text', '')):
                logger.info(f"Duplicate signal ignored in zone {zone}")
                return {
                    "success": True,
                    "status": "success",
                    "data": {
                        "signal_id": None,
                        "message": "Duplicate activity ignored",
                        "rejected": True,
                        "reason": "duplicate",
                    }
                }
        else:
            # Expect structured fields
            zone = (request.zone or 'UNKNOWN').upper()
            activity = request.activity_type or 'unknown'
            time_window = request.time_window or 'unknown'
            location = request.location or 'Local area' if hasattr(request, 'location') else 'Local area'
            crop = ''
            original_text = request.raw_text or ''

        # Parse timestamp with validation
        try:
            if request.timestamp:
                timestamp = datetime.fromisoformat(request.timestamp.replace('Z', '+00:00'))
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

        signal = Signal(
            id=signal_id,
            zone=zone,
            activity_type=activity,
            sector=sector,
            time_window=time_window,
            timestamp=timestamp,
            source=normalize_signal_source(request.source or "web"),
            original_text=original_text or ''
        )
        db.add(signal)
        db.commit()
        db.refresh(signal)

        logger.info(f"Signal saved: {signal.id} {signal.activity_type} {signal.zone}")

        return {
            "success": True,
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
            "success": False,
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
