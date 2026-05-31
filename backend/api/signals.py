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

        # If raw_text is provided, normalize it
        if request.raw_text:
            from backend.utils.signal_normalizer import normalize_signal_text
            normalized = normalize_signal_text(request.raw_text)
            zone = (request.zone or normalized.get('zone') or 'UNKNOWN').upper()
            activity = normalized.get('activity_type') or request.activity_type or 'unknown'
            time_window = normalized.get('time_window') or request.time_window or 'unknown'
            location = normalized.get('location') or 'Local area'
            crop = normalized.get('crop', '') or ''
            original_text = normalized.get('original_text', request.raw_text) or ''
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

        # Store signal in database (include original_text)
        # Anti-spam: limit signals per user per zone in the last hour
        try:
            recent_window = datetime.utcnow() - timedelta(hours=1)
            recent_count = db.query(Signal).filter(
                Signal.user_id == (request.user_id if request.user_id else "anonymous"),
                Signal.zone == zone,
                Signal.timestamp >= recent_window
            ).count()
            if recent_count >= 5:
                logger.warning(f"Spam detected: user {request.user_id} exceeded limit in zone {zone}")
                raise HTTPException(status_code=429, detail="Too many signals submitted recently. Please wait before sending more.")
        except HTTPException:
            raise
        except Exception:
            # If the DB check fails for any reason, proceed but log
            logger.warning("Could not perform spam check; continuing")

        # Duplicate identical message check (same user, same zone, same original_text within 1 hour)
        try:
            if original_text:
                dup = db.query(Signal).filter(
                    Signal.user_id == (request.user_id if request.user_id else "anonymous"),
                    Signal.zone == zone,
                    Signal.original_text == original_text,
                    Signal.timestamp >= recent_window
                ).first()
                if dup:
                    logger.info(f"Duplicate signal ignored for user {request.user_id} in zone {zone}")
                    return {
                        "success": True,
                        "status": "success",
                        "data": {
                            "signal_id": dup.id,
                            "message": "Duplicate activity ignored"
                        }
                    }
        except Exception:
            logger.warning("Could not perform duplicate-check; continuing")

        signal = Signal(
            id=signal_id,
            zone=zone,
            activity_type=activity,
            sector=sector,
            time_window=time_window,
            timestamp=timestamp,
            source=request.source or "web",
            user_id=request.user_id if request.user_id else "anonymous",
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
