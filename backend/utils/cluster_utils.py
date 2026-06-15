"""
Cluster utilities — whitelist-validated geographic clustering only.
"""
import re
from typing import List, Dict, Any, Optional

from backend.utils.zone_whitelist import (
    ZONE_SUBZONES,
    resolve_sub_zone,
    validate_sub_zone,
    PILOT_ZONES,
)

ACTIVITY_SYNONYMS = {
    'irrigation': ['irrigation', 'pump', 'water', 'watering', 'sprinkler'],
    'trading': ['trade', 'trading', 'sell', 'sold', 'buy', 'buying', 'market', 'shop'],
    'milling': ['milling', 'mill', 'grind', 'grinding'],
    'welding': ['welding', 'weld', 'metalwork', 'forge'],
    'storage': ['storage', 'store', 'warehouse', 'cold storage', 'cold chain'],
    'farming': ['farm', 'farming', 'grow', 'growing', 'plant', 'planting', 'harvest', 'harvesting'],
}

GAP_BY_ACTIVITY = {
    'irrigation': ('No reliable three-phase irrigation supply', 'Solar pump irrigation cluster'),
    'farming': ('No reliable irrigation system', 'Community irrigation scheme'),
    'storage': ('No cold chain or warehouse facility', 'Community storage warehouse'),
    'milling': ('No local milling or processing facility', 'Local grain milling facility'),
    'trading': ('No organized market access', 'Market access hub for local trade'),
    'welding': ('No reliable workshop power supply', 'Community workshop with reliable power'),
    'energy': ('Insufficient grid capacity', 'Solar mini-grid deployment'),
}


def _infer_demand_pattern(time_windows, signal_count: int) -> str:
    if isinstance(time_windows, set):
        windows_set = time_windows
    else:
        windows_set = set(time_windows or [])
    windows = sorted(windows_set - {'unknown'})
    window_label = ', '.join(windows) if windows else 'mixed windows'
    cycles = min(max(signal_count, 1), 7)
    return f"{window_label.title()} peaks, {cycles} of 7 cycles"


def _compute_cluster_confidence(signal_count: int, activity_counts: Dict[str, int]) -> float:
    if signal_count <= 0:
        return 0.0
    top_count = max(activity_counts.values()) if activity_counts else 0
    density = min(signal_count / 7.0, 1.0)
    concentration = top_count / max(signal_count, 1)
    return round(min(0.95, 0.35 + (0.4 * density) + (0.25 * concentration)), 2)


def _resolve_signal_sub_zone(signal: Dict[str, Any]) -> Optional[str]:
    zone = (signal.get('zone') or 'MZUZU').upper()
    if zone not in PILOT_ZONES:
        return None

    if signal.get('sub_zone'):
        validated = validate_sub_zone(zone, signal['sub_zone'])
        if validated:
            return validated

    location = signal.get('location') or ''
    text = signal.get('original_text') or signal.get('normalized_text') or ''
    sub_zone, is_valid = resolve_sub_zone(zone, location, text)
    return sub_zone if is_valid else None


def build_cluster_summary(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Group signals by (zone + validated sub_zone).
    Signals without a whitelisted sub-zone are excluded from clusters.
    """
    clusters: Dict[str, Dict[str, Any]] = {}

    for signal in signals:
        if not signal or not isinstance(signal, dict):
            continue

        zone = (signal.get('zone') or 'MZUZU').upper()
        if zone not in PILOT_ZONES:
            continue

        sub_zone = _resolve_signal_sub_zone(signal)
        if not sub_zone:
            continue

        activity = (signal.get('activity_type') or signal.get('activity') or 'unknown').lower()
        if activity == 'unknown':
            continue

        time_window = signal.get('time_window') or 'unknown'
        cluster_id = f"{zone}-{sub_zone.replace(' ', '_')}"
        key = cluster_id

        if key not in clusters:
            clusters[key] = {
                'cluster_id': key,
                'cluster_name': f"{sub_zone} Cluster",
                'zone': zone,
                'sub_zone': sub_zone,
                'activities': {},
                'time_windows': set(),
                'signal_count': 0,
            }

        cluster = clusters[key]
        cluster['signal_count'] += 1
        cluster['activities'][activity] = cluster['activities'].get(activity, 0) + 1
        if time_window:
            cluster['time_windows'].add(time_window)

    results: List[Dict[str, Any]] = []
    for cluster in clusters.values():
        if cluster['signal_count'] < 1:
            continue

        activity_counts = cluster['activities']
        top_activities = sorted(activity_counts.items(), key=lambda x: x[1], reverse=True)
        dominant_activity = top_activities[0][0] if top_activities else 'farming'

        gap, project = GAP_BY_ACTIVITY.get(
            dominant_activity,
            ('No dedicated local infrastructure identified yet', 'Reliable power access for cluster activities'),
        )

        cluster['dominant_activity'] = dominant_activity
        cluster['top_activities'] = [a for a, _ in top_activities]
        cluster['demand_pattern'] = _infer_demand_pattern(cluster['time_windows'], cluster['signal_count'])
        cluster['key_gap'] = gap
        cluster['recommended_project'] = project
        cluster['infrastructure_gaps'] = [gap]
        cluster['recommended_projects'] = [project]
        cluster['confidence_score'] = _compute_cluster_confidence(cluster['signal_count'], activity_counts)
        cluster['time_windows'] = sorted(cluster['time_windows'])
        cluster['summary'] = (
            f"{cluster['sub_zone']}: {dominant_activity} activity, "
            f"{cluster['signal_count']} signals, {cluster['demand_pattern']}."
        )
        results.append(cluster)

    return sorted(results, key=lambda c: c['signal_count'], reverse=True)
