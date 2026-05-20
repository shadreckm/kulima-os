"""
Summary endpoints
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime

router = APIRouter()


@router.get("/summary/{zone}")
async def get_summary(zone: str):
    """
    Return coordination summary for a zone.
    
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
        # TODO: Query database for coordination summary
        # TODO: Return summary data
        
        return {
            "zone": zone,
            "total_patterns": 0,
            "high_confidence_patterns": 0,
            "moderate_confidence_patterns": 0,
            "zones_with_coordinated_demand": [],
            "productive_activities_detected": [],
            "key_finding": "No patterns detected yet",
            "updated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
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
