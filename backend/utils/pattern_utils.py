"""
Pattern utilities for basic signal aggregation
"""
from typing import List, Dict, Any


def generate_basic_patterns(signal_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate basic patterns by grouping signals by activity_type and time_window.
    
    This provides a simple, reliable pattern detection that guarantees
    patterns exist whenever signals exist.
    
    Args:
        signal_data: List of signal dictionaries with activity_type, time_window, zone, cycle_index
        
    Returns:
        List of pattern dictionaries
    """
    patterns = []
    
    # Group signals by (activity_type, time_window)
    grouped = {}
    for s in signal_data:
        key = (s["activity_type"], s["time_window"])
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(s)
    
    # Generate patterns from grouped signals
    for i, ((activity, time), group) in enumerate(grouped.items()):
        patterns.append({
            "activity_type": activity,
            "time_window": time,
            "count": len(group),
            "zone": group[0]["zone"],
            "cycle_index": i
        })
    
    return patterns


def get_productive_activities(patterns: List[Dict[str, Any]]) -> List[str]:
    """
    Extract unique activity types from patterns.
    
    Args:
        patterns: List of pattern dictionaries
        
    Returns:
        List of unique activity types
    """
    return list(set(p["activity_type"] for p in patterns))
