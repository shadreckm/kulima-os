"""
Summary endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import Signal
from core.lumoza.lumoza_engine import LumozaEngine
from core.lundai.lundai_engine import LundaiEngine
from core.zentari.zentari_engine import ZentariEngine
from policy import compute_planning_reserve

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
        print(f"Running coordination pipeline for zone: {zone}")
        
        # 1. Fetch signals from database
        signals = db.query(Signal).filter(Signal.zone == zone.upper()).all()
        print(f"Found {len(signals)} signals in database for zone {zone}")
        
        if not signals:
            return {
                "zone": zone,
                "total_patterns": 0,
                "high_confidence_patterns": 0,
                "moderate_confidence_patterns": 0,
                "zones_with_coordinated_demand": [],
                "productive_activities_detected": [],
                "key_finding": "No signals detected yet",
                "updated_at": datetime.utcnow().isoformat()
            }
        
        # 2. Convert database signals to engine format
        signal_data = []
        for signal in signals:
            signal_data.append({
                "zone": signal.zone,
                "activity_type": signal.activity_type,
                "time_window": signal.time_window,
                "timestamp": signal.timestamp.isoformat(),
                "source": signal.source
            })
        
        # Add cycle_index to each signal
        for i, signal in enumerate(signal_data):
            signal["cycle_index"] = i
        
        print(f"Converted {len(signal_data)} signals to engine format with cycle_index")
        
        # 3. Run LUMOZA engine to generate coordination patterns
        print("Running LUMOZA engine...")
        lumoza = LumozaEngine()
        patterns = lumoza.process_signals(signal_data)
        print(f"LUMOZA generated {len(patterns)} patterns")
        
        if not patterns:
            return {
                "zone": zone,
                "total_patterns": 0,
                "high_confidence_patterns": 0,
                "moderate_confidence_patterns": 0,
                "zones_with_coordinated_demand": [],
                "productive_activities_detected": [],
                "key_finding": "No coordination patterns detected",
                "updated_at": datetime.utcnow().isoformat()
            }
        
        # 4. Run LUNDAI engine for spatial validation
        print("Running LUNDAI engine...")
        lundai = LundaiEngine()
        planning_reserve = compute_planning_reserve(len(patterns))
        lundai_analysis = lundai.analyze_settlement_context(patterns, planning_reserve=planning_reserve)
        print(f"LUNDAI analysis complete")
        
        # 5. Run ZENTARI engine for confidence scoring
        print("Running ZENTARI engine...")
        zentari = ZentariEngine()
        confidence_results = zentari.evaluate_coordination_confidence(patterns, planning_reserve=planning_reserve)
        print(f"ZENTARI evaluated {len(confidence_results)} patterns")
        
        # 6. Compute summary metrics
        total_patterns = len(confidence_results)
        high_confidence_patterns = sum(1 for r in confidence_results if r.get("confidence_class") == "high")
        moderate_confidence_patterns = sum(1 for r in confidence_results if r.get("confidence_class") == "moderate")
        
        productive_activities = list(set(p.get("activity_type") for p in patterns))
        
        key_finding = "Strong coordination patterns detected" if high_confidence_patterns >= 3 else \
                      "Emerging coordination patterns detected" if high_confidence_patterns >= 1 else \
                      "Insufficient coordination for infrastructure planning"
        
        print(f"Summary computed: {total_patterns} total, {high_confidence_patterns} high confidence")
        
        return {
            "zone": zone,
            "total_patterns": total_patterns,
            "high_confidence_patterns": high_confidence_patterns,
            "moderate_confidence_patterns": moderate_confidence_patterns,
            "zones_with_coordinated_demand": [zone] if total_patterns > 0 else [],
            "productive_activities_detected": productive_activities,
            "key_finding": key_finding,
            "updated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"Error in summary pipeline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/zones")
async def get_zones():
    """
    List all available zones.
    
    Response:
    {
      "zones": ["MZUZU", "LILONGWE", "BLANTYRE", "ZOMBA"],
      "total": 4
    }
    """
    try:
        # TODO: Query database for all zones
        return {
            "zones": ["MZUZU", "LILONGWE", "BLANTYRE", "ZOMBA"],
            "total": 4
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
