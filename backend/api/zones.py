"""
Zone and Metadata Endpoints
Provides zone-specific data, patterns, and infrastructure insights
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import List, Dict, Optional
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database.connection import get_db
from backend.database.models import Signal, Pattern, Zone
from core.lumoza.lumoza_engine import LumozaEngine
from core.zentari.zentari_engine import ZentariEngine
from core.lundai.lundai_engine import LundaiEngine, evaluate_signal_integrity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Define zone metadata
ZONE_METADATA = {
    "MZUZU": {
        "name": "Mzuzu",
        "region": "Northern Region",
        "settlement_type": "Semi-rural",
        "population_estimate": 150000,
        "primary_activities": ["irrigation", "milling", "trading"],
        "infrastructure_status": "basic"
    },
    "LILONGWE": {
        "name": "Lilongwe",
        "region": "Central Region",
        "settlement_type": "Urban",
        "population_estimate": 1200000,
        "primary_activities": ["trading", "storage", "cold storage"],
        "infrastructure_status": "moderate"
    },
    "BLANTYRE": {
        "name": "Blantyre",
        "region": "Southern Region",
        "settlement_type": "Urban",
        "population_estimate": 900000,
        "primary_activities": ["milling", "welding", "trading"],
        "infrastructure_status": "moderate"
    },
    "ZOMBA": {
        "name": "Zomba",
        "region": "Southern Region",
        "settlement_type": "Rural",
        "population_estimate": 120000,
        "primary_activities": ["irrigation", "storage", "trading"],
        "infrastructure_status": "basic"
    }
}


@router.get("/zone/{zone}")
async def get_zone_data(zone: str, db: Session = Depends(get_db)):
    """
    Get comprehensive zone data including metadata and current status.
    
    Response:
    {
      "status": "success",
      "data": {
        "zone": "MZUZU",
        "metadata": {...},
        "signal_count": 42,
        "active_patterns": 3,
        "last_signal_timestamp": "2026-05-20T10:00:00Z"
      }
    }
    """
    try:
        zone_upper = zone.upper()
        
        if zone_upper not in ZONE_METADATA:
            raise HTTPException(
                status_code=404,
                detail=f"Zone {zone} not found. Valid zones: {', '.join(ZONE_METADATA.keys())}"
            )
        
        # Get zone metadata
        metadata = ZONE_METADATA[zone_upper]
        
        # Count signals for this zone
        signal_count = db.query(func.count(Signal.id)).filter(Signal.zone == zone_upper).scalar()
        
        # Count patterns for this zone
        pattern_count = db.query(func.count(Pattern.id)).filter(Pattern.zone == zone_upper).scalar()
        
        # Get last signal timestamp
        last_signal = db.query(Signal).filter(Signal.zone == zone_upper).order_by(Signal.timestamp.desc()).first()
        last_signal_timestamp = last_signal.timestamp.isoformat() if last_signal else None
        
        # Get activity type distribution
        activity_distribution = db.query(
            Signal.activity_type,
            func.count(Signal.id).label('count')
        ).filter(Signal.zone == zone_upper).group_by(Signal.activity_type).all()
        
        activities = [
            {
                "type": activity,
                "count": count
            }
            for activity, count in activity_distribution
        ]
        
        logger.info(f"Retrieved zone data for {zone_upper}: {signal_count} signals")
        
        return {
            "success": True,
            "status": "success",
            "data": {
                "zone": zone_upper,
                "metadata": metadata,
                "signal_count": signal_count,
                "pattern_count": pattern_count,
                "activity_distribution": activities,
                "last_signal_timestamp": last_signal_timestamp,
                "retrieved_at": datetime.utcnow().isoformat()
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving zone data: {e}")
        return {
            "success": False,
            "status": "error",
            "message": str(e)
        }


@router.get("/patterns/{zone}")
async def get_patterns(zone: str, db: Session = Depends(get_db)):
    """
    Get detected coordination patterns for a zone.
    
    Response:
    {
      "status": "success",
      "data": {
        "zone": "MZUZU",
        "patterns": [
          {
            "id": "pat_123",
            "activity_type": "irrigation",
            "confidence_class": "high",
            "stability_score": 0.85,
            "demand_rhythm": {...},
            "created_at": "2026-05-20T10:00:00Z"
          }
        ],
        "summary": {
          "total": 5,
          "high_confidence": 3,
          "moderate_confidence": 2
        }
      }
    }
    """
    try:
        zone_upper = zone.upper()
        
        # Fetch patterns from database
        patterns = db.query(Pattern).filter(Pattern.zone == zone_upper).order_by(Pattern.created_at.desc()).all()
        
        # Count by confidence level
        high_confidence_count = len([p for p in patterns if p.confidence_class == "high"])
        moderate_confidence_count = len([p for p in patterns if p.confidence_class == "moderate"])
        low_confidence_count = len([p for p in patterns if p.confidence_class == "low"])
        
        # Build response
        pattern_data = []
        for p in patterns:
            import json
            try:
                demand_rhythm = json.loads(p.demand_rhythm) if isinstance(p.demand_rhythm, str) else p.demand_rhythm
            except:
                demand_rhythm = {}
            
            pattern_data.append({
                "id": p.id,
                "activity_type": p.activity_type,
                "confidence_class": p.confidence_class,
                "stability_score": p.stability_score,
                "demand_rhythm": demand_rhythm,
                "evaluation_window": p.evaluation_window,
                "created_at": p.created_at.isoformat()
            })
        
        logger.info(f"Retrieved {len(patterns)} patterns for zone {zone_upper}")
        
        return {
            "success": True,
            "status": "success",
            "data": {
                "zone": zone_upper,
                "patterns": pattern_data,
                "summary": {
                    "total": len(patterns),
                    "high_confidence": high_confidence_count,
                    "moderate_confidence": moderate_confidence_count,
                    "low_confidence": low_confidence_count
                },
                "retrieved_at": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving patterns: {e}")
        return {
            "success": False,
            "status": "error",
            "message": str(e)
        }


@router.get("/infrastructure-gaps/{zone}")
async def get_infrastructure_gaps(zone: str, db: Session = Depends(get_db)):
    """
    Get infrastructure gap analysis for a zone (LUNDAI analysis).
    
    Response:
    {
      "status": "success",
      "data": {
        "zone": "MZUZU",
        "gaps": [
          {
            "activity_type": "irrigation",
            "coordination_strength": 0.8,
            "infrastructure_status": "insufficient",
            "recommendation": "High-capacity three-phase lines needed",
            "priority": "high"
          }
        ]
      }
    }
    """
    try:
        zone_upper = zone.upper()
        
        # Get zone metadata
        metadata = ZONE_METADATA.get(zone_upper, {})
        infrastructure_status = metadata.get("infrastructure_status", "unknown")
        
        # Get signals to analyze
        signals = db.query(Signal).filter(Signal.zone == zone_upper).all()
        
        if not signals:
            return {
                "success": True,
                "status": "success",
                "data": {
                    "zone": zone_upper,
                    "gaps": [],
                    "summary": {
                        "critical_gaps": 0,
                        "total_gaps": 0
                    },
                    "analysis": "Insufficient signal data to perform infrastructure gap analysis"
                }
            }
        
        # Analyze coordination patterns by activity
        activity_counts = {}
        for signal in signals:
            activity = signal.activity_type
            activity_counts[activity] = activity_counts.get(activity, 0) + 1
        
        # Generate gap analysis based on activity patterns and infrastructure status
        gaps = []
        total_signals = len(signals)
        
        # Energy demand profiles by activity
        activity_profiles = {
            "irrigation": {"energy_intensive": True, "capacity_needed": "50-100 kW", "phase_requirement": "three-phase"},
            "milling": {"energy_intensive": True, "capacity_needed": "10-50 kW", "phase_requirement": "three-phase or single-phase"},
            "cold storage": {"energy_intensive": True, "capacity_needed": "20-100 kW", "phase_requirement": "three-phase"},
            "welding": {"energy_intensive": True, "capacity_needed": "5-15 kW", "phase_requirement": "single-phase or three-phase"},
            "trading": {"energy_intensive": False, "capacity_needed": "1-5 kW", "phase_requirement": "single-phase"},
            "storage": {"energy_intensive": False, "capacity_needed": "2-10 kW", "phase_requirement": "single-phase"}
        }
        
        for activity, count in activity_counts.items():
            coordination_strength = min(count / max(total_signals, 1), 1.0)
            profile = activity_profiles.get(activity, {"energy_intensive": False, "capacity_needed": "unknown"})
            
            # Determine if there's a gap
            has_gap = coordination_strength > 0.3 and profile.get("energy_intensive", False)
            
            if has_gap or count > 2:
                gap = {
                    "activity_type": activity,
                    "coordination_strength": round(coordination_strength, 2),
                    "signal_count": count,
                    "infrastructure_status": infrastructure_status,
                    "energy_requirement": profile.get("capacity_needed", "unknown"),
                    "phase_requirement": profile.get("phase_requirement", "unknown"),
                    "recommendation": _get_infrastructure_recommendation(activity, infrastructure_status),
                    "priority": _calculate_priority(coordination_strength, profile.get("energy_intensive", False))
                }
                gaps.append(gap)
        
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        gaps.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 999))
        
        critical_gaps = len([g for g in gaps if g.get("priority") == "critical"])
        
        logger.info(f"Infrastructure gap analysis for {zone_upper}: {len(gaps)} gaps identified")
        
        return {
            "success": True,
            "status": "success",
            "data": {
                "zone": zone_upper,
                "gaps": gaps,
                "summary": {
                    "critical_gaps": critical_gaps,
                    "total_gaps": len(gaps),
                    "infrastructure_baseline": infrastructure_status
                },
                "analysis": _get_gap_analysis_summary(gaps, zone_upper),
                "retrieved_at": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error analyzing infrastructure gaps: {e}")
        return {
            "success": False,
            "status": "error",
            "message": str(e)
        }


def _get_infrastructure_recommendation(activity: str, current_infrastructure: str) -> str:
    """Generate infrastructure recommendation based on activity type."""
    recommendations = {
        "irrigation": {
            "basic": "Install high-capacity transformer and three-phase distribution lines for irrigation demand",
            "moderate": "Upgrade three-phase capacity for peak irrigation season demand",
            "advanced": "Deploy smart metering and load balancing for efficient irrigation power distribution"
        },
        "milling": {
            "basic": "Install dedicated milling circuit with appropriate three-phase capacity",
            "moderate": "Upgrade to handle concurrent milling operations during peak harvest season",
            "advanced": "Deploy predictive load management for milling operations"
        },
        "cold storage": {
            "basic": "Install dedicated three-phase line for continuous cold storage operation",
            "moderate": "Upgrade to ensure reliable 24/7 cold chain supply",
            "advanced": "Deploy backup power and smart cooling management systems"
        },
        "welding": {
            "basic": "Install single or three-phase welding circuit depending on demand",
            "moderate": "Upgrade to handle concurrent welding operations",
            "advanced": "Deploy smart power distribution for welding load management"
        }
    }
    
    activity_recs = recommendations.get(activity, {})
    return activity_recs.get(current_infrastructure, "Conduct detailed infrastructure assessment")


def _calculate_priority(coordination_strength: float, energy_intensive: bool) -> str:
    """Calculate infrastructure priority based on coordination strength and intensity."""
    if energy_intensive:
        if coordination_strength >= 0.7:
            return "critical"
        elif coordination_strength >= 0.5:
            return "high"
        elif coordination_strength >= 0.3:
            return "medium"
    else:
        if coordination_strength >= 0.5:
            return "medium"
        elif coordination_strength >= 0.3:
            return "low"
    return "low"


def _get_gap_analysis_summary(gaps: List[Dict], zone: str) -> str:
    """Generate human-readable summary of gap analysis."""
    if not gaps:
        return f"No significant infrastructure gaps detected in {zone}. Current infrastructure may be adequate."
    
    critical_count = len([g for g in gaps if g.get("priority") == "critical"])
    high_count = len([g for g in gaps if g.get("priority") == "high"])
    
    if critical_count > 0:
        return f"Critical infrastructure gaps identified in {zone}. {critical_count} high-priority activity type(s) require immediate infrastructure upgrade."
    elif high_count > 0:
        return f"Significant infrastructure needs identified in {zone}. {high_count} activity type(s) would benefit from infrastructure investment."
    else:
        return f"Moderate infrastructure enhancement opportunities identified in {zone}."
