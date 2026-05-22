"""
Summary endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import List, Dict
import logging
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import Signal
from core.lumoza.lumoza_engine import LumozaEngine
from core.lundai.lundai_engine import LundaiEngine, evaluate_signal_integrity
from core.zentari.zentari_engine import ZentariEngine
from policy import compute_planning_reserve

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
        logger.info(f"Running full coordination pipeline for zone: {zone}")
        
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
                "signal_source": signal.source,
                "user_phone": signal.user_id,
                "service_priority": "productive"
            })
        
        # Add cycle_index to each signal
        for i, signal in enumerate(signal_data):
            signal["cycle_index"] = i
        
        logger.info(f"Converted {len(signal_data)} signals to engine format with cycle_index")
        
        # 3. Run LUMOZA engine for pattern detection
        logger.info("Running LUMOZA engine...")
        lumoza = LumozaEngine()
        coordination_patterns = lumoza.process_signals(signal_data)
        logger.info(f"LUMOZA generated {len(coordination_patterns)} coordination patterns")
        
        if not coordination_patterns:
            return {
                "status": "success",
                "data": {
                    "zone": zone,
                    "total_patterns": 0,
                    "high_confidence_patterns": 0,
                    "moderate_confidence_patterns": 0,
                    "zones_with_coordinated_demand": [],
                    "productive_activities_detected": [],
                    "key_finding": "No coordination patterns detected yet",
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        
        # 4. Run LUNDAI engine for integrity evaluation
        logger.info("Running LUNDAI engine for integrity evaluation...")
        integrity_results = evaluate_signal_integrity(signal_data, integrity_threshold=0.4)
        logger.info(f"LUNDAI evaluated {len(integrity_results)} activity-zone groups")
        
        # Merge integrity scores into coordination patterns
        pattern_map = {(p['activity_type'], p['zone'], p['time_window']): p for p in coordination_patterns}
        for integrity_result in integrity_results:
            key = (integrity_result['activity'], integrity_result['zone'], 'morning')  # Simplified key matching
            if key in pattern_map:
                pattern_map[key]['integrity_score'] = integrity_result['integrity_score']
                pattern_map[key]['alignment_level'] = integrity_result['classification']
                pattern_map[key]['signal_count'] = integrity_result['signal_count']
                pattern_map[key]['unique_days'] = integrity_result['unique_days']
                pattern_map[key]['unique_senders'] = integrity_result['unique_senders']
        
        # 5. Run LUNDAI engine for settlement context analysis
        logger.info("Running LUNDAI engine for settlement context...")
        lundai = LundaiEngine()
        planning_reserve = compute_planning_reserve(len(coordination_patterns))
        lundai_analysis = lundai.analyze_settlement_context(coordination_patterns, planning_reserve)
        logger.info(f"LUNDAI completed settlement context analysis")
        
        # Extract flow graph from LUNDAI analysis
        flow_graph = lundai_analysis.get('flow_graph', {})
        logger.info(f"Flow graph contains {flow_graph.get('total_nodes', 0)} nodes and {flow_graph.get('total_edges', 0)} edges")
        
        # 6. Run ZENTARI engine for coordination confidence evaluation
        logger.info("Running ZENTARI engine for coordination confidence...")
        zentari = ZentariEngine()
        confidence_results = zentari.evaluate_coordination_confidence(coordination_patterns, planning_reserve, flow_graph=flow_graph)
        logger.info(f"ZENTARI evaluated {len(confidence_results)} patterns for coordination confidence")
        
        # 7. Compute summary metrics from full pipeline output
        total_patterns = len(confidence_results)
        high_confidence_patterns = sum(1 for r in confidence_results if r['confidence_class'] == 'high')
        moderate_confidence_patterns = sum(1 for r in confidence_results if r['confidence_class'] == 'moderate')
        
        productive_activities = list(set(p['activity_type'] for p in confidence_results))
        
        # Generate key finding from pipeline output
        if high_confidence_patterns > 0:
            key_finding = f"Strong coordination patterns detected with {high_confidence_patterns} high-confidence activities"
        elif moderate_confidence_patterns > 0:
            key_finding = f"Emerging coordination patterns detected with {moderate_confidence_patterns} moderate-confidence activities"
        else:
            key_finding = "Coordination patterns detected but require additional validation"
        
        logger.info(f"Summary computed: {total_patterns} total, {high_confidence_patterns} high confidence, {moderate_confidence_patterns} moderate confidence")
        
        # Calculate risk model from confidence results
        risk_model = _calculate_risk_model(confidence_results, lundai_analysis)
        
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
                "updated_at": datetime.utcnow().isoformat(),
                "pipeline_output": {
                    "coordination_patterns": coordination_patterns,
                    "lundai_analysis": lundai_analysis,
                    "flow_graph": flow_graph,
                    "confidence_results": confidence_results,
                    "risk_model": risk_model
                }
            }
        }
    except Exception as e:
        logger.error(f"Error in summary pipeline: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "data": {
                "error": str(e)
            }
        }


@router.get("/flow-graph/{zone}")
async def get_flow_graph(zone: str, db: Session = Depends(get_db)):
    """
    Return flow graph for visualization.
    
    Response:
    {
      "zone": "MZUZU",
      "nodes": [...],
      "edges": [...],
      "total_nodes": 5,
      "total_edges": 8
    }
    """
    try:
        logger.info(f"Generating flow graph for zone: {zone}")
        
        # Fetch signals from database
        signals = db.query(Signal).filter(Signal.zone == zone.upper()).all()
        logger.info(f"Found {len(signals)} signals in database for zone {zone}")
        
        if not signals:
            return {
                "status": "success",
                "data": {
                    "zone": zone,
                    "nodes": [],
                    "edges": [],
                    "total_nodes": 0,
                    "total_edges": 0
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
        
        # Run LUMOZA engine for pattern detection
        logger.info("Running LUMOZA engine...")
        lumoza = LumozaEngine()
        coordination_patterns = lumoza.process_signals(signal_data)
        logger.info(f"LUMOZA generated {len(coordination_patterns)} coordination patterns")
        
        if not coordination_patterns:
            return {
                "status": "success",
                "data": {
                    "zone": zone,
                    "nodes": [],
                    "edges": [],
                    "total_nodes": 0,
                    "total_edges": 0
                }
            }
        
        # Run LUNDAI engine for flow graph generation
        logger.info("Running LUNDAI engine for flow graph...")
        lundai = LundaiEngine()
        planning_reserve = compute_planning_reserve(len(coordination_patterns))
        lundai_analysis = lundai.analyze_settlement_context(coordination_patterns, planning_reserve)
        
        # Extract flow graph
        flow_graph = lundai_analysis.get('flow_graph', {})
        
        logger.info(f"Flow graph generated: {flow_graph.get('total_nodes', 0)} nodes, {flow_graph.get('total_edges', 0)} edges")
        
        return {
            "status": "success",
            "data": {
                "zone": zone,
                "nodes": flow_graph.get('nodes', []),
                "edges": flow_graph.get('edges', []),
                "total_nodes": flow_graph.get('total_nodes', 0),
                "total_edges": flow_graph.get('total_edges', 0)
            }
        }
    except Exception as e:
        logger.error(f"Error generating flow graph: {str(e)}")
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
        planning_reserve = compute_planning_reserve(len(coordination_patterns))
        lundai_analysis = lundai.analyze_settlement_context(coordination_patterns, planning_reserve)
        flow_graph = lundai_analysis.get('flow_graph', {})
        
        zentari = ZentariEngine()
        confidence_results = zentari.evaluate_coordination_confidence(coordination_patterns, planning_reserve, flow_graph=flow_graph)
        
        # Calculate zone score
        from core.decision.decision_engine import DecisionEngine
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


@router.get("/regional-analysis")
async def get_regional_analysis(db: Session = Depends(get_db)):
    """
    Return regional coordination analysis across all zones.
    
    Response:
    {
      "zone_scores": {...},
      "inter_zone_flows": [...],
      "regional_flow_network": {...}
    }
    """
    try:
        logger.info("Generating regional coordination analysis")
        
        # Fetch all signals from database
        signals = db.query(Signal).all()
        logger.info(f"Found {len(signals)} signals in database")
        
        if not signals:
            return {
                "status": "success",
                "data": {
                    "zone_scores": {},
                    "inter_zone_flows": [],
                    "regional_flow_network": {"nodes": [], "edges": [], "total_nodes": 0, "total_edges": 0}
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
        
        # Run full pipeline for all zones
        lumoza = LumozaEngine()
        coordination_patterns = lumoza.process_signals(signal_data)
        
        if not coordination_patterns:
            return {
                "status": "success",
                "data": {
                    "zone_scores": {},
                    "inter_zone_flows": [],
                    "regional_flow_network": {"nodes": [], "edges": [], "total_nodes": 0, "total_edges": 0}
                }
            }
        
        lundai = LundaiEngine()
        planning_reserve = compute_planning_reserve(len(coordination_patterns))
        lundai_analysis = lundai.analyze_settlement_context(coordination_patterns, planning_reserve)
        flow_graph = lundai_analysis.get('flow_graph', {})
        
        zentari = ZentariEngine()
        confidence_results = zentari.evaluate_coordination_confidence(coordination_patterns, planning_reserve, flow_graph=flow_graph)
        
        # Calculate zone scores for all zones
        from core.decision.decision_engine import DecisionEngine
        decision_engine = DecisionEngine()
        zone_scores = {}
        
        # Group patterns by zone
        patterns_by_zone = {}
        for pattern in coordination_patterns:
            zone = pattern['zone']
            if zone not in patterns_by_zone:
                patterns_by_zone[zone] = []
            patterns_by_zone[zone].append(pattern)
        
        for zone, zone_patterns in patterns_by_zone.items():
            zone_score = decision_engine._calculate_zone_score(zone_patterns, confidence_results, flow_graph)
            zone_scores[zone] = zone_score
        
        # Detect inter-zone flows
        from core.flow.cross_zone_flow_detector import CrossZoneFlowDetector
        flow_detector = CrossZoneFlowDetector()
        inter_zone_flows = flow_detector.detect_inter_zone_correlations(patterns_by_zone)
        regional_flow_network = flow_detector.build_regional_flow_network(patterns_by_zone)
        
        logger.info(f"Regional analysis generated: {len(zone_scores)} zones, {len(inter_zone_flows)} inter-zone flows")
        
        return {
            "status": "success",
            "data": {
                "zone_scores": zone_scores,
                "inter_zone_flows": inter_zone_flows,
                "regional_flow_network": regional_flow_network
            }
        }
    except Exception as e:
        logger.error(f"Error generating regional analysis: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "data": {
                "error": str(e)
            }
        }


@router.get("/infrastructure-roadmap")
async def get_infrastructure_roadmap(db: Session = Depends(get_db)):
    """
    Return infrastructure roadmap with phased rollout plan.
    
    Response:
    {
      "phased_rollout": {...},
      "load_distribution": {...},
      "ranked_zones": [...]
    }
    """
    try:
        logger.info("Generating infrastructure roadmap")
        
        # Fetch all signals from database
        signals = db.query(Signal).all()
        logger.info(f"Found {len(signals)} signals in database")
        
        if not signals:
            return {
                "status": "success",
                "data": {
                    "phased_rollout": {},
                    "load_distribution": {},
                    "ranked_zones": []
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
                    "phased_rollout": {},
                    "load_distribution": {},
                    "ranked_zones": []
                }
            }
        
        lundai = LundaiEngine()
        planning_reserve = compute_planning_reserve(len(coordination_patterns))
        lundai_analysis = lundai.analyze_settlement_context(coordination_patterns, planning_reserve)
        flow_graph = lundai_analysis.get('flow_graph', {})
        
        zentari = ZentariEngine()
        confidence_results = zentari.evaluate_coordination_confidence(coordination_patterns, planning_reserve, flow_graph=flow_graph)
        
        # Use Infrastructure Design Layer to generate roadmap
        from core.infrastructure.infrastructure_design import InfrastructureDesignLayer
        from core.decision.decision_engine import DecisionEngine
        
        design_layer = InfrastructureDesignLayer()
        decision_engine = DecisionEngine()
        
        # Get zone scores
        patterns_by_zone = {}
        for pattern in coordination_patterns:
            zone = pattern['zone']
            if zone not in patterns_by_zone:
                patterns_by_zone[zone] = []
            patterns_by_zone[zone].append(pattern)
        
        zone_scores = {}
        for zone, zone_patterns in patterns_by_zone.items():
            zone_score = decision_engine._calculate_zone_score(zone_patterns, confidence_results, flow_graph)
            zone_scores[zone] = zone_score
        
        # Rank zones by priority
        ranked_zones = design_layer.rank_zones_by_priority(zone_scores)
        
        # Get infrastructure needs
        infrastructure_needs = []
        for result in confidence_results:
            infrastructure_needs.append({
                'zone': result.get('zone'),
                'activity_type': result.get('activity_type'),
                'recommended_capacity_kw': design_layer.determine_infrastructure_type(result.get('activity_type'))['base_capacity_kw']
            })
        
        # Design phased rollout
        phased_rollout = design_layer.design_phased_rollout(ranked_zones, infrastructure_needs)
        
        # Estimate load distribution
        zones = list(zone_scores.keys())
        infrastructure_types = list(set([design_layer.determine_infrastructure_type(result.get('activity_type'))['type'] for result in confidence_results]))
        load_distribution = design_layer.estimate_load_distribution(zones, infrastructure_types)
        
        logger.info(f"Infrastructure roadmap generated: {len(ranked_zones)} zones, {phased_rollout['total_timeline_months']} months timeline")
        
        return {
            "status": "success",
            "data": {
                "phased_rollout": phased_rollout,
                "load_distribution": load_distribution,
                "ranked_zones": ranked_zones
            }
        }
    except Exception as e:
        logger.error(f"Error generating infrastructure roadmap: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "data": {
                "error": str(e)
            }
        }


def _calculate_risk_model(confidence_results: List[Dict], lundai_analysis: Dict) -> Dict:
    """
    Calculate multi-factor risk model based on persistence, stability, and flow strength.
    """
    risk_factors = []
    
    # Analyze persistence
    persistence_values = [r.get('persistence', 0) for r in confidence_results]
    avg_persistence = sum(persistence_values) / len(persistence_values) if persistence_values else 0
    
    if avg_persistence < 0.4:
        risk_factors.append({
            "type": "Demand uncertainty risk",
            "severity": "high" if avg_persistence < 0.2 else "moderate",
            "description": f"Low persistence ({avg_persistence:.2f}) indicates patterns may not repeat consistently"
        })
    elif avg_persistence < 0.6:
        risk_factors.append({
            "type": "Demand uncertainty risk",
            "severity": "low",
            "description": f"Moderate persistence ({avg_persistence:.2f}) requires monitoring"
        })
    
    # Analyze stability
    stability_values = [r.get('stability_score', 0) for r in confidence_results]
    avg_stability = sum(stability_values) / len(stability_values) if stability_values else 0
    
    if avg_stability < 0.4:
        risk_factors.append({
            "type": "Volatility risk",
            "severity": "high" if avg_stability < 0.2 else "moderate",
            "description": f"Low stability ({avg_stability:.2f}) indicates high variance in pattern occurrence"
        })
    elif avg_stability < 0.6:
        risk_factors.append({
            "type": "Volatility risk",
            "severity": "low",
            "description": f"Moderate stability ({avg_stability:.2f}) indicates some pattern variance"
        })
    
    # Analyze flow strength
    flow_strength_values = [r.get('flow_strength', 0) for r in confidence_results]
    avg_flow_strength = sum(flow_strength_values) / len(flow_strength_values) if flow_strength_values else 0
    
    if avg_flow_strength < 0.3:
        risk_factors.append({
            "type": "Fragmentation risk",
            "severity": "high",
            "description": f"Weak flow connections ({avg_flow_strength:.2f}) indicate fragmented economic activity"
        })
    elif avg_flow_strength < 0.5:
        risk_factors.append({
            "type": "Fragmentation risk",
            "severity": "moderate",
            "description": f"Moderate flow strength ({avg_flow_strength:.2f}) indicates partial value chain integration"
        })
    
    # Analyze signal density
    total_patterns = len(confidence_results)
    if total_patterns < 3:
        risk_factors.append({
            "type": "Data insufficiency risk",
            "severity": "high",
            "description": f"Low pattern count ({total_patterns}) indicates insufficient data for reliable planning"
        })
    elif total_patterns < 5:
        risk_factors.append({
            "type": "Data insufficiency risk",
            "severity": "moderate",
            "description": f"Limited pattern count ({total_patterns}) requires additional data collection"
        })
    
    # Calculate overall risk level
    high_risk_count = sum(1 for rf in risk_factors if rf.get("severity") == "high")
    moderate_risk_count = sum(1 for rf in risk_factors if rf.get("severity") == "moderate")
    
    if high_risk_count >= 2:
        risk_level = "high"
        recommendation = "Significant risks detected. Recommend extensive data collection and monitoring before infrastructure commitment."
    elif high_risk_count >= 1 or moderate_risk_count >= 2:
        risk_level = "moderate"
        recommendation = "Moderate risks present. Recommend phased deployment with continued monitoring and validation."
    else:
        risk_level = "low"
        recommendation = "Low risk profile. Patterns show good persistence, stability, and flow integration. Suitable for infrastructure planning."
    
    return {
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "recommendation": recommendation,
        "risk_metrics": {
            "average_persistence": round(avg_persistence, 2),
            "average_stability": round(avg_stability, 2),
            "average_flow_strength": round(avg_flow_strength, 2),
            "total_patterns": total_patterns
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
