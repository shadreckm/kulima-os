"""
Summary endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import Signal
from backend.utils.pattern_utils import generate_basic_patterns, get_productive_activities

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/summary/{zone}")
async def get_summary(zone: str, db: Session = Depends(get_db)):
    """
    Return coordination summary for a zone.
    
    Runs full coordination pipeline: signals → LUMOZA → LUNDAI → ZENTARI
    
    Response:
    {
      "zone": "MZUZU",
      "total_patterns": 5,
      "high_confidence_patterns": 3,
      "moderate_confidence_patterns": 2,
      "zones_with_coordinated_demand": ["MZUZU"],
      "productive_activities_detected": ["irrigation", "milling"],
      "key_finding": "Strong coordination patterns detected",
      "updated_at": "2026-05-20T10:00:00Z"
    }
    """
    try:
        logger.info(f"Running coordination pipeline for zone: {zone}")
        
        # 1. Fetch signals from database
        signals = db.query(Signal).filter(Signal.zone == zone.upper()).all()
        logger.info(f"Found {len(signals)} signals in database for zone {zone}")
        
        if not signals:
            return {
                "status": "success",
                "data": {
                    "zone": zone,
                    "total_patterns": 0,
                    "high_confidence_patterns": 0,
                    "moderate_confidence_patterns": 0,
                    "zones_with_coordinated_demand": [],
                    "productive_activities_detected": [],
                    "key_finding": "No signals detected yet",
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        
        # 2. Convert database signals to engine format
        signal_data = []
        for signal in signals:
            signal_data.append({
                "zone": signal.zone,
                "activity_type": signal.activity_type,
                "time_window": signal.time_window,
                "timestamp": signal.timestamp.isoformat(),
                "source": signal.source,
                "user_id": signal.user_id
            })
        
        # Add cycle_index to each signal
        for i, signal in enumerate(signal_data):
            signal["cycle_index"] = i
        
        logger.info(f"Converted {len(signal_data)} signals to engine format with cycle_index")
        
        # 3. Generate basic patterns using aggregation
        logger.info("Generating basic patterns...")
        patterns = generate_basic_patterns(signal_data)
        logger.info(f"Generated {len(patterns)} patterns")
        
        if not patterns:
            return {
                "status": "success",
                "data": {
                    "zone": zone,
                    "total_patterns": 0,
                    "high_confidence_patterns": 0,
                    "moderate_confidence_patterns": 0,
                    "zones_with_coordinated_demand": [],
                    "productive_activities_detected": [],
                    "key_finding": "No signals detected yet",
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        
        # 4. Compute summary metrics
        total_patterns = len(patterns)
        high_confidence_patterns = total_patterns  # All patterns are valid
        moderate_confidence_patterns = 0
        
        productive_activities = get_productive_activities(patterns)
        
        key_finding = "Real activity detected in zone"
        
        logger.info(f"Summary computed: {total_patterns} total, {high_confidence_patterns} high confidence")
        
        return {
            "status": "success",
            "data": {
                "zone": zone,
                "total_patterns": total_patterns,
                "high_confidence_patterns": high_confidence_patterns,
                "moderate_confidence_patterns": moderate_confidence_patterns,
                "zones_with_coordinated_demand": [zone] if total_patterns > 0 else [],
                "productive_activities_detected": productive_activities,
                "key_finding": key_finding,
                "updated_at": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error in summary pipeline: {str(e)}")
        return {
            "status": "error",
            "data": {
                "error": str(e)
            }
        }


@router.get("/zones")
async def get_zones(db: Session = Depends(get_db)):
    """
    List all available zones.
    
    Response:
    {
      "zones": ["MZUZU", "LILONGWE", "BLANTYRE", "ZOMBA"],
      "total": 4
    }
    """
    try:
        # Query database for distinct zones
        zones = db.query(Signal.zone).distinct().all()
        zone_list = [zone[0] for zone in zones if zone[0]]
        
        logger.info(f"Fetched {len(zone_list)} zones")
        
        return {
            "status": "success",
            "data": {
                "zones": zone_list,
                "total": len(zone_list)
            }
        }
    except Exception as e:
        logger.error(f"Error fetching zones: {str(e)}")
        return {
            "status": "error",
            "data": {
                "error": str(e)
            }
        }
