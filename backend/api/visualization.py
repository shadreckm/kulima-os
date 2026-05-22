"""
KULIMA OS Pilot - Visualization Data API
========================================

API endpoints for visualization data including time-series, flow networks, and pattern evolution.

INVARIANT ENFORCEMENT:
- Zero-PII: Returns only aggregated patterns (never raw signals)
- Coordination > Identity: Visualization of collective patterns, not individual tracking
- Semantic Guard: Designed for infrastructure planning, not surveillance or profiling
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import Signal
import logging

from core.lumoza.lumoza_engine import LumozaEngine
from core.lundai.lundai_engine import LundaiEngine
from core.zentari.zentari_engine import ZentariEngine
from core.temporal.long_horizon_model import LongHorizonModel
from core.flow.cross_zone_flow_detector import CrossZoneFlowDetector
from core.decision.decision_engine import DecisionEngine

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/time-series/{zone}")
async def get_time_series(zone: str, activity_type: str = None, db: Session = Depends(get_db)):
    """
    Return time-series data for a zone.
    
    Query Parameters:
    - zone: Zone identifier (e.g., MZUZU)
    - activity_type: Optional activity type filter (e.g., irrigation)
    
    Response:
    [
      {
        "timestamp": "2026-01-01",
        "activity_type": "irrigation",
        "zone": "MZUZU",
        "frequency": 5,
        "persistence": 0.75,
        "stability": 0.68
      }
    ]
    """
    try:
        logger.info(f"Generating time-series data for zone: {zone}, activity: {activity_type}")
        
        # Fetch signals from database
        signals = db.query(Signal).filter(Signal.zone == zone.upper()).all()
        logger.info(f"Found {len(signals)} signals in database for zone {zone}")
        
        if not signals:
            return {
                "status": "success",
                "data": []
            }
        
        # Convert database signals to engine format
        signal_data = []
        for signal in signals:
            signal_data.append({
                "zone": signal.zone,
                "activity_type": signal.activity_type,
                "time_window": signal.time_window,
                "timestamp": signal.timestamp.isoformat(),
                "signal_source": signal.source,
                "user_phone": signal.user_id,
                "service_priority": "productive"
            })
        
        # Add cycle_index to each signal
        for i, signal in enumerate(signal_data):
            signal["cycle_index"] = i
        
        # Run LUMOZA engine for pattern detection
        logger.info("Running LUMOZA engine...")
        lumoza = LumozaEngine()
        coordination_patterns = lumoza.process_signals(signal_data)
        logger.info(f"LUMOZA generated {len(coordination_patterns)} coordination patterns")
        
        # Use Long-Horizon Model to generate time-series
        long_horizon = LongHorizonModel()
        
        # Add weekly patterns to history
        weekly_data = {
            'timestamp': signal_data[0]['timestamp'] if signal_data else '2026-01-01',
            'patterns': coordination_patterns
        }
        long_horizon.add_weekly_patterns(coordination_patterns, weekly_data['timestamp'])
        
        # Generate time-series
        time_series = long_horizon.generate_time_series(zone.upper(), activity_type)
        
        # Filter by activity type if specified
        if activity_type:
            time_series = [ts for ts in time_series if ts['activity_type'] == activity_type]
        
        logger.info(f"Generated {len(time_series)} time-series data points")
        
        return {
            "status": "success",
            "data": time_series
        }
    except Exception as e:
        logger.error(f"Error generating time-series data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "data": {
                "error": str(e)
            }
        }


@router.get("/flow-network")
async def get_flow_network(db: Session = Depends(get_db)):
    """
    Return regional flow network with nodes and edges.
    
    Response:
    {
      "nodes": [...],
      "edges": [...],
      "total_nodes": 5,
      "total_edges": 8
    }
    """
    try:
        logger.info("Generating regional flow network")
        
        # Fetch all signals from database
        signals = db.query(Signal).all()
        logger.info(f"Found {len(signals)} signals in database")
        
        if not signals:
            return {
                "status": "success",
                "data": {
                    "nodes": [],
                    "edges": [],
                    "total_nodes": 0,
                    "total_edges": 0
                }
            }
        
        # Group signals by zone
        patterns_by_zone = {}
        for signal in signals:
            zone = signal.zone
            if zone not in patterns_by_zone:
                patterns_by_zone[zone] = []
            
            patterns_by_zone[zone].append({
                'activity_type': signal.activity_type,
                'zone': zone,
                'pattern_frequency': 1,
                'pattern_persistence': 0.5,
                'confidence_score': 50,
                'temporal_weight': 1.0,
                'persistence_weight': 1.0,
                'time_window': signal.time_window
            })
        
        # Run Cross-Zone Flow Detector
        logger.info("Running Cross-Zone Flow Detector...")
        flow_detector = CrossZoneFlowDetector()
        flow_network = flow_detector.build_regional_flow_network(patterns_by_zone)
        
        logger.info(f"Generated flow network: {flow_network['total_nodes']} nodes, {flow_network['total_edges']} edges")
        
        return {
            "status": "success",
            "data": flow_network
        }
    except Exception as e:
        logger.error(f"Error generating flow network: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "data": {
                "error": str(e)
            }
        }


@router.get("/pattern-evolution/{activity_type}")
async def get_pattern_evolution(activity_type: str, db: Session = Depends(get_db)):
    """
    Return pattern evolution over time for a specific activity type.
    
    Query Parameters:
    - activity_type: Activity type (e.g., irrigation)
    
    Response:
    [
      {
        "timestamp": "2026-01-01",
        "activity_type": "irrigation",
        "zone": "MZUZU",
        "frequency": 5,
        "persistence": 0.75,
        "stability": 0.68,
        "trend": "increasing"
      }
    ]
    """
    try:
        logger.info(f"Generating pattern evolution for activity: {activity_type}")
        
        # Fetch signals from database
        signals = db.query(Signal).filter(Signal.activity_type == activity_type.lower()).all()
        logger.info(f"Found {len(signals)} signals for activity {activity_type}")
        
        if not signals:
            return {
                "status": "success",
                "data": []
            }
        
        # Group signals by zone and timestamp
        patterns_by_zone = {}
        for signal in signals:
            zone = signal.zone
            if zone not in patterns_by_zone:
                patterns_by_zone[zone] = []
            
            patterns_by_zone[zone].append({
                'activity_type': signal.activity_type,
                'zone': zone,
                'pattern_frequency': 1,
                'pattern_persistence': 0.5,
                'pattern_stability': 0.5,
                'timestamp': signal.timestamp.isoformat()
            })
        
        # Generate pattern evolution data
        pattern_evolution = []
        for zone, zone_patterns in patterns_by_zone.items():
            for pattern in zone_patterns:
                pattern_evolution.append({
                    'timestamp': pattern['timestamp'],
                    'activity_type': pattern['activity_type'],
                    'zone': pattern['zone'],
                    'frequency': pattern['pattern_frequency'],
                    'persistence': pattern['pattern_persistence'],
                    'stability': pattern['pattern_stability'],
                    'trend': 'stable'  # Placeholder for trend
                })
        
        # Sort by timestamp
        pattern_evolution.sort(key=lambda x: x['timestamp'])
        
        logger.info(f"Generated {len(pattern_evolution)} pattern evolution data points")
        
        return {
            "status": "success",
            "data": pattern_evolution
        }
    except Exception as e:
        logger.error(f"Error generating pattern evolution: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "data": {
                "error": str(e)
            }
        }


@router.get("/zone-scorecard/{zone}")
async def get_zone_scorecard(zone: str, db: Session = Depends(get_db)):
    """
    Return zone scorecard with persistence, stability, and coordination strength.
    
    Response:
    {
      "zone": "MZUZU",
      "persistence_score": 0.75,
      "stability_score": 0.68,
      "coordination_strength": 0.82,
      "overall_rating": 0.75,
      "rating_category": "high"
    }
    """
    try:
        logger.info(f"Generating zone scorecard for zone: {zone}")
        
        # Fetch signals from database
        signals = db.query(Signal).filter(Signal.zone == zone.upper()).all()
        logger.info(f"Found {len(signals)} signals in database for zone {zone}")
        
        if not signals:
            return {
                "status": "success",
                "data": {
                    "zone": zone,
                    "persistence_score": 0.0,
                    "stability_score": 0.0,
                    "coordination_strength": 0.0,
                    "overall_rating": 0.0,
                    "rating_category": "low"
                }
            }
        
        # Convert database signals to engine format
        signal_data = []
        for signal in signals:
            signal_data.append({
                "zone": signal.zone,
                "activity_type": signal.activity_type,
                "time_window": signal.time_window,
                "timestamp": signal.timestamp.isoformat(),
                "signal_source": signal.source,
                "user_phone": signal.user_id,
                "service_priority": "productive"
            })
        
        # Add cycle_index to each signal
        for i, signal in enumerate(signal_data):
            signal["cycle_index"] = i
        
        # Run full pipeline
        lumoza = LumozaEngine()
        coordination_patterns = lumoza.process_signals(signal_data)
        
        if not coordination_patterns:
            return {
                "status": "success",
                "data": {
                    "zone": zone,
                    "persistence_score": 0.0,
                    "stability_score": 0.0,
                    "coordination_strength": 0.0,
                    "overall_rating": 0.0,
                    "rating_category": "low"
                }
            }
        
        lundai = LundaiEngine()
        from backend.utils.pattern_utils import compute_planning_reserve
        planning_reserve = compute_planning_reserve(len(coordination_patterns))
        lundai_analysis = lundai.analyze_settlement_context(coordination_patterns, planning_reserve)
        flow_graph = lundai_analysis.get('flow_graph', {})
        
        zentari = ZentariEngine()
        confidence_results = zentari.evaluate_coordination_confidence(coordination_patterns, planning_reserve, flow_graph=flow_graph)
        
        # Calculate zone score
        decision_engine = DecisionEngine()
        zone_score = decision_engine._calculate_zone_score(coordination_patterns, confidence_results, flow_graph)
        
        logger.info(f"Zone scorecard generated: {zone_score}")
        
        return {
            "status": "success",
            "data": {
                "zone": zone,
                **zone_score
            }
        }
    except Exception as e:
        logger.error(f"Error generating zone scorecard: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "data": {
                "error": str(e)
            }
        }
